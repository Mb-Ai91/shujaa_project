from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from core.manager.service import ShujaaManager
from core.runtime.process_registry import ProcessRegistry
from core.runtime.process_registry_contract import (
    CleanupDisposition,
    CleanupResult,
    ProcessOwnership,
)
from core.tasks.store import TaskRecord
from core.work.event_store import InMemoryEventStore
from core.work.events import AppendResult
from core.work.models import Execution, ExecutionStatus


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runner must not be called.")


def _seed_running_task_with_owner(
    manager: ShujaaManager,
    *,
    task_id: str,
    execution_id: str,
    work_id: str = "work-seed",
    pid: int = 4101,
    pgid: int = 4201,
    start_ticks: int = 4301,
) -> ProcessOwnership:
    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=work_id,
            command="test-command",
            status="running",
            process_id=pid,
            process_group_id=pgid,
        )
    )
    manager.execution_registry.create(
        Execution(
            execution_id=execution_id,
            work_id=work_id,
            task_id=task_id,
        )
    )
    manager._transition_execution(
        execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id=f"{execution_id}:running",
    )
    owner = ProcessOwnership(
        task_id=task_id,
        execution_id=execution_id,
        pid=pid,
        pgid=pgid,
        process_start_time_ticks=start_ticks,
    )
    manager.process_registry.register(owner)
    return owner


def test_cleanup_event_identity_derivation_properties():
    """Verify behavioral identity properties of cleanup event derivation."""
    same_1 = ShujaaManager._cleanup_event_id("op-1", "task-1")
    same_2 = ShujaaManager._cleanup_event_id("op-1", "task-1")
    diff_task = ShujaaManager._cleanup_event_id("op-1", "task-2")
    diff_op = ShujaaManager._cleanup_event_id("op-2", "task-1")

    assert same_1 == same_2
    assert same_1 != diff_task
    assert same_1 != diff_op


def test_cancel_task_emits_cleanup_event_after_cleanup(tmp_path):
    registry = ProcessRegistry(tmp_path / "processes.json")
    store = InMemoryEventStore()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
        event_store=store,
    )
    manager._read_process_start_time_ticks = lambda pid: 4301
    manager._terminate_process_group_by_id = lambda pgid: None

    task_id = "task-cancel-event-1"
    execution_id = "exec-cancel-event-1"
    cleanup_op_id = "op-cancel-cleanup-1"

    _seed_running_task_with_owner(
        manager,
        task_id=task_id,
        execution_id=execution_id,
    )

    manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_stage5_cleanup_lifecycle_events-1",
        cleanup_operation_id=cleanup_op_id,
    )

    expected_event_id = manager._cleanup_event_id(
        cleanup_op_id,
        task_id,
    )
    matching_events = [
        entry.record
        for entry in store.list()
        if (
            entry.record.operation_id == cleanup_op_id
            and entry.record.task_id == task_id
        )
    ]

    assert len(matching_events) == 1
    assert matching_events[0].event_id == expected_event_id


def test_cleanup_registered_processes_emits_event_per_task(tmp_path):
    registry = ProcessRegistry(tmp_path / "processes.json")
    store = InMemoryEventStore()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
        event_store=store,
    )
    manager._read_process_start_time_ticks = lambda pid: 4301
    manager._terminate_process_group_by_id = lambda pgid: None

    task_1 = "task-multi-clean-1"
    task_2 = "task-multi-clean-2"
    cleanup_op_id = "op-startup-cleanup-batch"

    _seed_running_task_with_owner(
        manager,
        task_id=task_1,
        execution_id="exec-multi-1",
        pid=5101,
        pgid=5201,
    )
    _seed_running_task_with_owner(
        manager,
        task_id=task_2,
        execution_id="exec-multi-2",
        pid=5102,
        pgid=5202,
    )

    manager.cleanup_registered_processes(
        cleanup_operation_id=cleanup_op_id,
    )

    for task_id in (task_1, task_2):
        expected_event_id = manager._cleanup_event_id(
            cleanup_op_id,
            task_id,
        )
        matching_events = [
            entry.record
            for entry in store.list()
            if (
                entry.record.operation_id == cleanup_op_id
                and entry.record.task_id == task_id
            )
        ]
        assert len(matching_events) == 1
        assert matching_events[0].event_id == expected_event_id


def test_cleanup_event_idempotent_replay_through_manager_emission():
    store = InMemoryEventStore()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )
    cleanup_op_id = "op-replay-clean-1"
    task_id = "task-replay-1"
    result = CleanupResult(
        disposition=CleanupDisposition.TERMINATED_AND_RELEASED,
        ownership=ProcessOwnership(
            task_id=task_id,
            execution_id="exec-replay-1",
            pid=6101,
            pgid=6201,
            process_start_time_ticks=6301,
        ),
    )

    first_receipt = manager._append_cleanup_event(
        result,
        task_id=task_id,
        cleanup_operation_id=cleanup_op_id,
        trigger="registered_cleanup",
        work_id=None,
    )
    second_receipt = manager._append_cleanup_event(
        result,
        task_id=task_id,
        cleanup_operation_id=cleanup_op_id,
        trigger="registered_cleanup",
        work_id=None,
    )

    assert first_receipt.result is AppendResult.APPENDED
    assert second_receipt.result is AppendResult.IDEMPOTENT_REPLAY

    matching = [
        entry.record
        for entry in store.list()
        if (
            entry.record.operation_id == cleanup_op_id
            and entry.record.task_id == task_id
        )
    ]
    assert len(matching) == 1


def test_cleanup_event_identity_conflict_through_manager_emission():
    store = InMemoryEventStore()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )
    cleanup_op_id = "op-conflict-clean-1"
    task_id = "task-conflict-1"

    result_1 = CleanupResult(
        disposition=CleanupDisposition.TERMINATED_AND_RELEASED,
        ownership=ProcessOwnership(
            task_id=task_id,
            execution_id="exec-conflict-1",
            pid=7101,
            pgid=7201,
            process_start_time_ticks=7301,
        ),
    )
    result_2 = CleanupResult(
        disposition=CleanupDisposition.NOT_OWNED,
        ownership=None,
    )

    first_receipt = manager._append_cleanup_event(
        result_1,
        task_id=task_id,
        cleanup_operation_id=cleanup_op_id,
        trigger="registered_cleanup",
        work_id=None,
    )
    conflict_receipt = manager._append_cleanup_event(
        result_2,
        task_id=task_id,
        cleanup_operation_id=cleanup_op_id,
        trigger="registered_cleanup",
        work_id=None,
    )

    assert first_receipt.result is AppendResult.APPENDED
    assert conflict_receipt.result is AppendResult.IDENTITY_CONFLICT

    matching = [
        entry.record
        for entry in store.list()
        if (
            entry.record.operation_id == cleanup_op_id
            and entry.record.task_id == task_id
        )
    ]
    assert len(matching) == 1


def test_concurrent_cleanup_event_identical_emissions_are_replay_stable():
    store = InMemoryEventStore()
    manager_1 = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )
    manager_2 = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )

    cleanup_op_id = "op-concurrent-replay-clean-1"
    task_id = "task-concurrent-replay-1"
    result = CleanupResult(
        disposition=CleanupDisposition.TERMINATED_AND_RELEASED,
        ownership=ProcessOwnership(
            task_id=task_id,
            execution_id="exec-concurrent-replay-1",
            pid=8101,
            pgid=8201,
            process_start_time_ticks=8301,
        ),
    )

    def emit(manager):
        return manager._append_cleanup_event(
            result,
            task_id=task_id,
            cleanup_operation_id=cleanup_op_id,
            trigger="registered_cleanup",
            work_id=None,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(emit, (manager_1, manager_2)))

    assert sorted(
        receipt.result.value for receipt in receipts
    ) == sorted(
        [
            AppendResult.APPENDED.value,
            AppendResult.IDEMPOTENT_REPLAY.value,
        ]
    )

    matching = [
        entry.record
        for entry in store.list()
        if (
            entry.record.operation_id == cleanup_op_id
            and entry.record.task_id == task_id
        )
    ]
    assert len(matching) == 1


def test_concurrent_cleanup_event_conflicting_emissions_preserve_one_winner():
    store = InMemoryEventStore()
    manager_1 = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )
    manager_2 = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )

    cleanup_op_id = "op-concurrent-conflict-clean-1"
    task_id = "task-concurrent-conflict-1"

    result_1 = CleanupResult(
        disposition=CleanupDisposition.TERMINATED_AND_RELEASED,
        ownership=ProcessOwnership(
            task_id=task_id,
            execution_id="exec-concurrent-conflict-1",
            pid=9101,
            pgid=9201,
            process_start_time_ticks=9301,
        ),
    )
    result_2 = CleanupResult(
        disposition=CleanupDisposition.NOT_OWNED,
        ownership=None,
    )

    def emit(args):
        manager, result = args
        return manager._append_cleanup_event(
            result,
            task_id=task_id,
            cleanup_operation_id=cleanup_op_id,
            trigger="registered_cleanup",
            work_id=None,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(
            pool.map(
                emit,
                (
                    (manager_1, result_1),
                    (manager_2, result_2),
                ),
            )
        )

    assert sorted(
        receipt.result.value for receipt in receipts
    ) == sorted(
        [
            AppendResult.APPENDED.value,
            AppendResult.IDENTITY_CONFLICT.value,
        ]
    )

    matching = [
        entry.record
        for entry in store.list()
        if (
            entry.record.operation_id == cleanup_op_id
            and entry.record.task_id == task_id
        )
    ]
    assert len(matching) == 1


def test_cleanup_event_write_failure_does_not_rewrite_cleanup_outcome(tmp_path, monkeypatch):
    def failing_hasher(data):
        raise OSError("simulated write failure")

    registry = ProcessRegistry(tmp_path / "processes.json")
    store = InMemoryEventStore(
        integrity_hasher=failing_hasher,
    )
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
        event_store=store,
    )
    manager._read_process_start_time_ticks = lambda pid: 4301
    monkeypatch.setattr(
        "core.manager.service.os.getpgid",
        lambda pid: 4201,
    )
    manager._terminate_process_group_by_id = lambda pgid: None

    task_id = "task-cleanup-write-failure-1"
    execution_id = "exec-cleanup-write-failure-1"

    _seed_running_task_with_owner(
        manager,
        task_id=task_id,
        execution_id=execution_id,
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_stage5_cleanup_lifecycle_events-2",
        cleanup_operation_id="op-cleanup-write-failure-1",
    )

    assert response["status"] == "cancelled"
    assert registry.get(task_id) is None
    assert store.list() == ()

def test_independent_cleanup_attempts_require_distinct_operation_ids():
    store = InMemoryEventStore()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )
    task_id = "task-independent-1"
    result = CleanupResult(
        disposition=CleanupDisposition.NOT_OWNED,
        ownership=None,
    )

    receipt_1 = manager._append_cleanup_event(
        result,
        task_id=task_id,
        cleanup_operation_id="op-attempt-1",
        trigger="registered_cleanup",
        work_id=None,
    )
    receipt_2 = manager._append_cleanup_event(
        result,
        task_id=task_id,
        cleanup_operation_id="op-attempt-2",
        trigger="registered_cleanup",
        work_id=None,
    )

    assert receipt_1.result is AppendResult.APPENDED
    assert receipt_2.result is AppendResult.APPENDED

    matching_1 = [
        entry.record
        for entry in store.list()
        if (
            entry.record.operation_id == "op-attempt-1"
            and entry.record.task_id == task_id
        )
    ]
    matching_2 = [
        entry.record
        for entry in store.list()
        if (
            entry.record.operation_id == "op-attempt-2"
            and entry.record.task_id == task_id
        )
    ]
    assert len(matching_1) == 1
    assert len(matching_2) == 1
    assert matching_1[0].event_id != matching_2[0].event_id
