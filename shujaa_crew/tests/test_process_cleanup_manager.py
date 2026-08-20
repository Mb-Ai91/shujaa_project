import signal

import pytest

import core.manager.service as service_module
from core.manager.service import ShujaaManager
from core.runtime.process_registry import ProcessRegistry
from core.runtime.process_registry_contract import (
    ProcessOwnership,
)
from core.tasks.store import TaskRecord
from core.work.models import Execution, ExecutionStatus


class UnusedRunner:
    def start(self, topic):
        raise AssertionError("Runner must not start.")


@pytest.fixture(autouse=True)
def matching_process_group(monkeypatch):
    monkeypatch.setattr(
        service_module.os,
        "getpgid",
        lambda pid: 4201,
    )


def _seed(
    manager,
    registry,
    *,
    suffix,
    terminal_cancelled=False,
    owner_execution_id=None,
):
    task_id = f"task-{suffix}"
    execution_id = f"exec-{suffix}"

    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=f"work-{suffix}",
            command="test",
            status=(
                "cancelled"
                if terminal_cancelled
                else "running"
            ),
            process_id=4101,
            process_group_id=4201,
            error=(
                "Task cancelled by user."
                if terminal_cancelled
                else None
            ),
        )
    )
    manager.execution_registry.create(
        Execution(
            execution_id=execution_id,
            work_id=f"work-{suffix}",
            task_id=task_id,
        )
    )
    manager._transition_execution(
        execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id=f"{execution_id}:running",
    )

    if terminal_cancelled:
        manager._transition_execution(
            execution_id,
            target_status=ExecutionStatus.CANCELLED,
            operation_id=f"{execution_id}:cancelled",
        )

    owner = ProcessOwnership(
        task_id=task_id,
        execution_id=(
            owner_execution_id or execution_id
        ),
        pid=4101,
        pgid=4201,
        process_start_time_ticks=4301,
    )
    registry.register(owner)

    return task_id, execution_id, owner


def test_winning_cancel_terminates_and_releases_owner(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, _, _ = _seed(
        manager,
        registry,
        suffix="winning-cancel",
    )
    signals = []

    manager._read_process_start_time_ticks = (
        lambda pid: 4301
    )
    manager._terminate_process_group_by_id = (
        lambda pgid: signals.append(pgid)
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_process_cleanup_manager-1",
        cleanup_operation_id="op-test-cancel-winning",
    )

    assert response["status"] == "cancelled"
    assert (
        response["cleanup_disposition"]
        == "terminated_and_released"
    )
    assert response["cleanup_error"] is None
    assert signals == [4201]
    assert registry.get(task_id) is None


def test_idempotent_cancel_retries_pending_cleanup(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, _, _ = _seed(
        manager,
        registry,
        suffix="cancel-replay",
        terminal_cancelled=True,
    )
    signals = []

    manager._read_process_start_time_ticks = (
        lambda pid: 4301
    )
    manager._terminate_process_group_by_id = (
        lambda pgid: signals.append(pgid)
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_process_cleanup_manager-2",
        cleanup_operation_id="op-test-cancel-replay",
    )

    assert response["status"] == "cancelled"
    assert (
        response["cleanup_disposition"]
        == "terminated_and_released"
    )
    assert signals == [4201]
    assert registry.get(task_id) is None


def test_already_exited_process_releases_without_signal(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, _, _ = _seed(
        manager,
        registry,
        suffix="already-exited",
    )
    signals = []

    manager._read_process_start_time_ticks = (
        lambda pid: None
    )
    manager._terminate_process_group_by_id = (
        lambda pgid: signals.append(pgid)
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_process_cleanup_manager-3",
        cleanup_operation_id="op-test-cancel-already-exited",
    )

    assert response["status"] == "cancelled"
    assert (
        response["cleanup_disposition"]
        == "already_exited_and_released"
    )
    assert signals == []
    assert registry.get(task_id) is None


def test_process_identity_mismatch_retains_owner(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, _, owner = _seed(
        manager,
        registry,
        suffix="identity-mismatch",
    )
    signals = []

    manager._read_process_start_time_ticks = (
        lambda pid: 9999
    )
    manager._terminate_process_group_by_id = (
        lambda pgid: signals.append(pgid)
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_process_cleanup_manager-4",
        cleanup_operation_id="op-test-cancel-identity-mismatch",
    )

    assert response["status"] == "cancelled"
    assert (
        response["cleanup_disposition"]
        == "identity_mismatch"
    )
    assert signals == []
    assert registry.get(task_id) == owner


def test_termination_failure_retains_owner_and_winner(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix="termination-failure",
    )

    manager._read_process_start_time_ticks = (
        lambda pid: 4301
    )

    def fail_termination(pgid):
        raise PermissionError("termination denied")

    manager._terminate_process_group_by_id = fail_termination

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_process_cleanup_manager-5",
        cleanup_operation_id="op-test-cancel-termination-failure",
    )

    execution = manager.execution_registry.get(
        execution_id
    )

    assert response["status"] == "cancelled"
    assert (
        response["cleanup_disposition"]
        == "termination_failed_retained"
    )
    assert response["cleanup_error"] == "termination denied"
    assert registry.get(task_id) == owner
    assert execution is not None
    assert execution.status == ExecutionStatus.CANCELLED


def test_stale_execution_cannot_cleanup_newer_owner(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, _, newer_owner = _seed(
        manager,
        registry,
        suffix="newer-owner",
        owner_execution_id="exec-newer-owner-2",
    )
    signals = []

    manager._read_process_start_time_ticks = (
        lambda pid: 4301
    )
    manager._terminate_process_group_by_id = (
        lambda pgid: signals.append(pgid)
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_process_cleanup_manager-6",
        cleanup_operation_id="op-test-cancel-stale-owner",
    )

    assert response["status"] == "cancelled"
    assert (
        response["cleanup_disposition"]
        == "owner_mismatch"
    )
    assert signals == []
    assert registry.get(task_id) == newer_owner

def test_termination_raises_if_group_survives_sigkill(
    monkeypatch,
):
    calls = []

    def process_survives(process_group_id, sent_signal):
        calls.append((process_group_id, sent_signal))

    monkeypatch.setattr(
        service_module.os,
        "killpg",
        process_survives,
    )

    manager = ShujaaManager(crew_runner=UnusedRunner())
    manager.TERMINATION_GRACE_SECONDS = 0

    with pytest.raises(
        RuntimeError,
        match="survived SIGKILL",
    ):
        manager._terminate_process_group_by_id(5201)

    assert calls == [
        (5201, signal.SIGTERM),
        (5201, signal.SIGKILL),
        (5201, 0),
    ]


def test_termination_confirms_exit_after_sigkill(
    monkeypatch,
):
    calls = []

    def process_exits_after_kill(
        process_group_id,
        sent_signal,
    ):
        calls.append((process_group_id, sent_signal))

        if len(calls) == 3 and sent_signal == 0:
            raise ProcessLookupError

    monkeypatch.setattr(
        service_module.os,
        "killpg",
        process_exits_after_kill,
    )

    manager = ShujaaManager(crew_runner=UnusedRunner())
    manager.TERMINATION_GRACE_SECONDS = 0

    manager._terminate_process_group_by_id(5202)

    assert calls == [
        (5202, signal.SIGTERM),
        (5202, signal.SIGKILL),
        (5202, 0),
    ]

def test_identity_read_failure_retains_owner_and_winner(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix="identity-read-failure",
    )
    signals = []

    def fail_identity_read(pid):
        raise PermissionError("proc identity unreadable")

    manager._read_process_start_time_ticks = (
        fail_identity_read
    )
    manager._terminate_process_group_by_id = (
        lambda pgid: signals.append(pgid)
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_process_cleanup_manager-7",
        cleanup_operation_id="op-test-cancel-identity-read-failure",
    )

    execution = manager.execution_registry.get(
        execution_id
    )

    assert response["status"] == "cancelled"
    assert (
        response["cleanup_disposition"]
        == "identity_check_failed_retained"
    )
    assert (
        response["cleanup_error"]
        == "proc identity unreadable"
    )
    assert signals == []
    assert registry.get(task_id) == owner
    assert execution is not None
    assert execution.status == ExecutionStatus.CANCELLED




def test_cleanup_refuses_process_group_mismatch(
    tmp_path,
    monkeypatch,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, _, owner = _seed(
        manager,
        registry,
        suffix="process-group-mismatch",
    )
    signals = []

    manager._read_process_start_time_ticks = (
        lambda pid: 4301
    )
    monkeypatch.setattr(
        service_module.os,
        "getpgid",
        lambda pid: 9999,
    )
    manager._terminate_process_group_by_id = (
        lambda pgid: signals.append(pgid)
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_process_cleanup_manager-8",
        cleanup_operation_id="op-test-cancel-group-mismatch",
    )

    assert response["status"] == "cancelled"
    assert (
        response["cleanup_disposition"]
        == "process_group_mismatch"
    )
    assert signals == []
    assert registry.get(task_id) == owner


def test_startup_cleanup_reports_retained_failures(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id, _, owner = _seed(
        manager,
        registry,
        suffix="startup-cleanup-report",
    )

    def fail_identity_read(pid):
        raise PermissionError("startup identity unavailable")

    manager._read_process_start_time_ticks = fail_identity_read

    results = manager.cleanup_registered_processes(
        cleanup_operation_id="op-test-startup-cleanup",
    )

    assert isinstance(results, dict)
    assert task_id in results
    assert (
        results[task_id].disposition.value
        == "identity_check_failed_retained"
    )
    assert (
        results[task_id].error
        == "startup identity unavailable"
    )
    assert registry.get(task_id) == owner
