import subprocess
from threading import Event

import pytest

from core.manager.service import ShujaaManager
from core.runtime.process_registry import ProcessRegistry
from core.tasks.store import TaskRecord
from core.work.models import Execution, ExecutionStatus


def _seed(manager, *, suffix):
    task_id = f"task-{suffix}"
    execution_id = f"exec-{suffix}"

    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=f"work-{suffix}",
            command="test",
            status="queued",
        )
    )
    manager.execution_registry.create(
        Execution(
            execution_id=execution_id,
            work_id=f"work-{suffix}",
            task_id=task_id,
        )
    )

    return task_id, execution_id


@pytest.mark.parametrize(
    ("return_code", "expected_status"),
    [
        (0, ExecutionStatus.COMPLETED),
        (1, ExecutionStatus.FAILED),
    ],
)
def test_process_execution_registers_and_releases_owner(
    tmp_path,
    return_code,
    expected_status,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    observed_owners = []
    task_id_holder = []

    class Process:
        pid = 987654321

        def wait(self, timeout=None):
            observed_owners.append(
                registry.get(task_id_holder[0])
            )
            return return_code

    class Runner:
        def start(self, topic):
            return Process()

        def get_result(self, process):
            return "completed result"

        def get_error(self, code):
            return f"Exit code: {code}"

    manager = ShujaaManager(
        crew_runner=Runner(),
        process_registry=registry,
    )
    task_id, execution_id = _seed(
        manager,
        suffix=f"exit-{return_code}",
    )
    task_id_holder.append(task_id)

    manager._execute_task(
        task_id,
        execution_id,
        "test",
        Event(),
        None,
        None,
    )

    assert len(observed_owners) == 1
    observed = observed_owners[0]
    assert observed is not None
    assert observed.task_id == task_id
    assert observed.execution_id == execution_id
    assert observed.pid == Process.pid
    assert observed.pgid == Process.pid

    assert registry.get(task_id) is None

    execution = manager.execution_registry.get(execution_id)
    assert execution is not None
    assert execution.status == expected_status


def test_timeout_releases_matching_process_owner(tmp_path):
    registry = ProcessRegistry(tmp_path / "processes.json")
    observed_owners = []
    task_id_holder = []
    termination_calls = []

    class TimeoutProcess:
        pid = 987654322

        def wait(self, timeout=None):
            observed_owners.append(
                registry.get(task_id_holder[0])
            )
            raise subprocess.TimeoutExpired(
                cmd="test",
                timeout=timeout,
            )

    class Runner:
        def start(self, topic):
            return TimeoutProcess()

    manager = ShujaaManager(
        crew_runner=Runner(),
        process_registry=registry,
    )
    manager._terminate_process_group = (
        lambda process, pgid: termination_calls.append(pgid)
    )

    task_id, execution_id = _seed(
        manager,
        suffix="timeout-owner",
    )
    task_id_holder.append(task_id)

    manager._execute_task(
        task_id,
        execution_id,
        "test",
        Event(),
        None,
        None,
    )

    assert len(observed_owners) == 1
    observed = observed_owners[0]
    assert observed is not None
    assert observed.execution_id == execution_id

    assert termination_calls == [TimeoutProcess.pid]
    assert registry.get(task_id) is None

    execution = manager.execution_registry.get(execution_id)
    assert execution is not None
    assert execution.status == ExecutionStatus.TIMED_OUT


def test_error_after_process_exit_releases_owner(tmp_path):
    registry = ProcessRegistry(tmp_path / "processes.json")
    observed_owners = []
    task_id_holder = []

    class CompletedProcess:
        pid = 987654323

        def wait(self, timeout=None):
            observed_owners.append(
                registry.get(task_id_holder[0])
            )
            return 0

    class BrokenResultRunner:
        def start(self, topic):
            return CompletedProcess()

        def get_result(self, process):
            raise RuntimeError("result decoding failed")

    manager = ShujaaManager(
        crew_runner=BrokenResultRunner(),
        process_registry=registry,
    )
    task_id, execution_id = _seed(
        manager,
        suffix="post-exit-error",
    )
    task_id_holder.append(task_id)

    manager._execute_task(
        task_id,
        execution_id,
        "test",
        Event(),
        None,
        None,
    )

    assert len(observed_owners) == 1
    observed = observed_owners[0]
    assert observed is not None
    assert observed.execution_id == execution_id

    assert registry.get(task_id) is None

    task = manager.task_store.get(task_id)
    execution = manager.execution_registry.get(execution_id)

    assert task is not None
    assert task.status == "failed"
    assert task.error == "result decoding failed"
    assert execution is not None
    assert execution.status == ExecutionStatus.FAILED



def test_identity_capture_failure_terminates_unregistered_process(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    termination_calls = []

    class Process:
        pid = 987654331

        def wait(self, timeout=None):
            raise AssertionError(
                "Process must be terminated before wait."
            )

    class Runner:
        def start(self, topic):
            return Process()

    manager = ShujaaManager(
        crew_runner=Runner(),
        process_registry=registry,
    )

    def fail_identity_capture(pid):
        raise PermissionError("process identity unavailable")

    manager._read_process_start_time_ticks = (
        fail_identity_capture
    )
    manager._terminate_process_group = (
        lambda process, pgid: termination_calls.append(pgid)
    )

    task_id, execution_id = _seed(
        manager,
        suffix="identity-capture-failure",
    )

    manager._execute_task(
        task_id,
        execution_id,
        "test",
        Event(),
        None,
        None,
    )

    execution = manager.execution_registry.get(execution_id)

    assert termination_calls == [Process.pid]
    assert registry.get(task_id) is None
    assert execution is not None
    assert execution.status == ExecutionStatus.FAILED


def test_wait_error_terminates_and_releases_registered_owner(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    termination_calls = []

    class Process:
        pid = 987654332

        def wait(self, timeout=None):
            raise RuntimeError("wait failed unexpectedly")

    class Runner:
        def start(self, topic):
            return Process()

    manager = ShujaaManager(
        crew_runner=Runner(),
        process_registry=registry,
    )
    manager._terminate_process_group = (
        lambda process, pgid: termination_calls.append(pgid)
    )

    task_id, execution_id = _seed(
        manager,
        suffix="wait-error",
    )

    manager._execute_task(
        task_id,
        execution_id,
        "test",
        Event(),
        None,
        None,
    )

    execution = manager.execution_registry.get(execution_id)

    assert termination_calls == [Process.pid]
    assert registry.get(task_id) is None
    assert execution is not None
    assert execution.status == ExecutionStatus.FAILED
