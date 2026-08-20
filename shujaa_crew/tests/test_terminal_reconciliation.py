import subprocess
from threading import Event

from core.manager.service import ShujaaManager
from core.tasks.store import TaskRecord, TaskStore
from core.work.execution_registry import InMemoryExecutionRegistry
from core.work.execution_registry_contract import (
    TransitionDisposition,
    TransitionResult,
)
from core.work.models import Execution, ExecutionStatus


class _UnusedRunner:
    def start(self, topic: str):
        raise AssertionError("Runner must not start in this test.")


class _MutableRunner:
    def __init__(self):
        self.process = None

    def start(self, topic: str):
        assert self.process is not None
        return self.process

    def get_result(self, process):
        return "losing completion result"

    def get_error(self, return_code: int) -> str:
        return "losing failure error"


class _CallbackProcess:
    pid = 987654321

    def __init__(
        self,
        callback,
        *,
        return_code: int = 0,
        raises_timeout: bool = False,
    ):
        self.callback = callback
        self.return_code = return_code
        self.raises_timeout = raises_timeout

    def wait(self, timeout=None):
        self.callback()

        if self.raises_timeout:
            raise subprocess.TimeoutExpired(
                cmd="test",
                timeout=timeout,
            )

        return self.return_code


def _seed_task_and_execution(
    manager,
    *,
    suffix: str,
    task_status: str,
    execution_status: ExecutionStatus,
):
    task_id = f"task-{suffix}"
    execution_id = f"exec-{suffix}"

    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=f"work-{suffix}",
            command="test",
            status=task_status,
        )
    )
    manager.execution_registry.create(
        Execution(
            execution_id=execution_id,
            work_id=f"work-{suffix}",
            task_id=task_id,
        )
    )

    if execution_status != ExecutionStatus.QUEUED:
        manager._transition_execution(
            execution_id,
            target_status=ExecutionStatus.RUNNING,
            operation_id=f"{execution_id}:running",
        )

    if execution_status not in {
        ExecutionStatus.QUEUED,
        ExecutionStatus.RUNNING,
    }:
        manager._transition_execution(
            execution_id,
            target_status=execution_status,
            operation_id=(
                f"{execution_id}:{execution_status.value}"
            ),
        )

    return task_id, execution_id


def test_late_cancel_preserves_completed_execution_winner():
    manager = ShujaaManager(crew_runner=_UnusedRunner())
    task_id, execution_id = _seed_task_and_execution(
        manager,
        suffix="completed-before-cancel",
        task_status="running",
        execution_status=ExecutionStatus.COMPLETED,
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_terminal_reconciliation-1",
        cleanup_operation_id="op-test-cancel-late",
    )

    task = manager.task_store.get(task_id)
    execution = manager.execution_registry.get(execution_id)

    assert response["status"] == "completed"
    assert task is not None
    assert task.status == "completed"
    assert task.error is None
    assert execution is not None
    assert execution.status == ExecutionStatus.COMPLETED


def test_queued_cancel_transitions_execution_directly():
    manager = ShujaaManager(crew_runner=_UnusedRunner())
    task_id, execution_id = _seed_task_and_execution(
        manager,
        suffix="queued-cancel",
        task_status="queued",
        execution_status=ExecutionStatus.QUEUED,
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_terminal_reconciliation-2",
        cleanup_operation_id="op-test-cancel-queued",
    )

    task = manager.task_store.get(task_id)
    execution = manager.execution_registry.get(execution_id)

    assert response["status"] == "cancelled"
    assert task is not None
    assert task.status == "cancelled"
    assert execution is not None
    assert execution.status == ExecutionStatus.CANCELLED


def test_late_timeout_preserves_completed_execution_winner():
    runner = _MutableRunner()
    manager = ShujaaManager(crew_runner=runner)
    task_id, execution_id = _seed_task_and_execution(
        manager,
        suffix="completed-before-timeout",
        task_status="queued",
        execution_status=ExecutionStatus.QUEUED,
    )

    def complete_first():
        manager._transition_execution(
            execution_id,
            target_status=ExecutionStatus.COMPLETED,
            operation_id=f"{execution_id}:winner-completed",
        )

    runner.process = _CallbackProcess(
        complete_first,
        raises_timeout=True,
    )
    manager._terminate_process_group = (
        lambda process, process_group_id: None
    )

    manager._execute_task(
        task_id,
        execution_id,
        "test",
        Event(),
        None,
        None,
    )

    task = manager.task_store.get(task_id)
    execution = manager.execution_registry.get(execution_id)

    assert task is not None
    assert task.status == "completed"
    assert task.error is None
    assert execution is not None
    assert execution.status == ExecutionStatus.COMPLETED


def test_late_completion_preserves_cancelled_execution_winner():
    runner = _MutableRunner()
    manager = ShujaaManager(crew_runner=runner)
    task_id, execution_id = _seed_task_and_execution(
        manager,
        suffix="cancelled-before-completion",
        task_status="queued",
        execution_status=ExecutionStatus.QUEUED,
    )

    def cancel_first():
        manager._transition_execution(
            execution_id,
            target_status=ExecutionStatus.CANCELLED,
            operation_id=f"{execution_id}:winner-cancelled",
        )

    runner.process = _CallbackProcess(
        cancel_first,
        return_code=0,
    )

    manager._execute_task(
        task_id,
        execution_id,
        "test",
        Event(),
        None,
        None,
    )

    task = manager.task_store.get(task_id)
    execution = manager.execution_registry.get(execution_id)

    assert task is not None
    assert task.status == "cancelled"
    assert task.result is None
    assert execution is not None
    assert execution.status == ExecutionStatus.CANCELLED


def test_late_failure_preserves_completed_execution_winner():
    runner = _MutableRunner()
    manager = ShujaaManager(crew_runner=runner)
    task_id, execution_id = _seed_task_and_execution(
        manager,
        suffix="completed-before-failure",
        task_status="queued",
        execution_status=ExecutionStatus.QUEUED,
    )

    def complete_first():
        manager._transition_execution(
            execution_id,
            target_status=ExecutionStatus.COMPLETED,
            operation_id=f"{execution_id}:winner-completed",
        )

    runner.process = _CallbackProcess(
        complete_first,
        return_code=1,
    )

    manager._execute_task(
        task_id,
        execution_id,
        "test",
        Event(),
        None,
        None,
    )

    task = manager.task_store.get(task_id)
    execution = manager.execution_registry.get(execution_id)

    assert task is not None
    assert task.status == "completed"
    assert task.error is None
    assert execution is not None
    assert execution.status == ExecutionStatus.COMPLETED


class _StaleOnceRegistry(InMemoryExecutionRegistry):
    def __init__(self):
        super().__init__()
        self.cancel_attempts = 0

    def transition(
        self,
        execution_id,
        *,
        target_status,
        expected_version,
        operation_id,
        source,
        error=None,
        result=None,
    ):
        if target_status == ExecutionStatus.CANCELLED:
            self.cancel_attempts += 1

            if self.cancel_attempts == 1:
                current = self.get(execution_id)
                assert current is not None

                advanced = super().transition(
                    execution_id,
                    target_status=ExecutionStatus.RUNNING,
                    expected_version=current.state_version,
                    operation_id=(
                        f"{execution_id}:concurrent-running"
                    ),
                    source="test",
                )

                return TransitionResult(
                    applied=False,
                    disposition=(
                        TransitionDisposition.STALE_VERSION
                    ),
                    execution=advanced.execution,
                )

        return super().transition(
            execution_id,
            target_status=target_status,
            expected_version=expected_version,
            operation_id=operation_id,
            source=source,
            error=error,
            result=result,
        )


def test_cancel_retries_after_stale_nonterminal_version():
    registry = _StaleOnceRegistry()
    manager = ShujaaManager(
        crew_runner=_UnusedRunner(),
        execution_registry=registry,
    )
    task_id, execution_id = _seed_task_and_execution(
        manager,
        suffix="stale-cancel",
        task_status="queued",
        execution_status=ExecutionStatus.QUEUED,
    )

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_terminal_reconciliation-3",
        cleanup_operation_id="op-test-cancel-stale",
    )

    task = manager.task_store.get(task_id)
    execution = registry.get(execution_id)

    assert registry.cancel_attempts == 2
    assert response["status"] == "cancelled"
    assert task is not None
    assert task.status == "cancelled"
    assert execution is not None
    assert execution.status == ExecutionStatus.CANCELLED


class _CountingRegistry(InMemoryExecutionRegistry):
    def __init__(self):
        super().__init__()
        self.cancel_attempts = 0

    def transition(self, execution_id, **kwargs):
        if (
            kwargs["target_status"]
            == ExecutionStatus.CANCELLED
        ):
            self.cancel_attempts += 1

        return super().transition(execution_id, **kwargs)


def test_idempotent_cancel_replay_is_consumed_explicitly():
    registry = _CountingRegistry()
    manager = ShujaaManager(
        crew_runner=_UnusedRunner(),
        execution_registry=registry,
    )
    task_id, execution_id = _seed_task_and_execution(
        manager,
        suffix="idempotent-cancel",
        task_status="running",
        execution_status=ExecutionStatus.CANCELLED,
    )
    registry.cancel_attempts = 0

    response = manager.cancel_task(
        task_id,
        cancel_operation_id="op-test-cancel-request-test_terminal_reconciliation-4",
        cleanup_operation_id="op-test-cancel-replay",
    )

    task = manager.task_store.get(task_id)
    execution = registry.get(execution_id)

    assert registry.cancel_attempts == 1
    assert response["status"] == "cancelled"
    assert task is not None
    assert task.status == "cancelled"
    assert execution is not None
    assert (
        execution.terminal_operation_id
        == f"{execution_id}:cancelled"
    )


def test_task_store_can_explicitly_clear_terminal_payload():
    store = TaskStore()
    task_id = "task-clear-terminal-payload"

    store.create(
        TaskRecord(
            task_id=task_id,
            command="test",
            status="failed",
            error="old error",
            result="old result",
        )
    )

    store.update(
        task_id,
        status="completed",
        error=None,
        result=None,
    )

    task = store.get(task_id)

    assert task is not None
    assert task.status == "completed"
    assert task.error is None
    assert task.result is None
