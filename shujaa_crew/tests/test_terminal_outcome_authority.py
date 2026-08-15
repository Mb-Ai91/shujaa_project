from dataclasses import replace

import pytest

from core.manager.service import ShujaaManager
from core.tasks.store import TaskRecord
from core.work.models import Execution, ExecutionStatus


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runner must not be called.")


def make_manager(suffix):
    manager = ShujaaManager(crew_runner=UnusedRunner())
    task_id = f"task-{suffix}"
    execution_id = f"exec-{suffix}"

    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=f"work-{suffix}",
            command="test terminal outcome",
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
    manager._transition_execution(
        execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id=f"{execution_id}:running",
    )
    manager.task_store.update(
        task_id,
        status="running",
    )

    return manager, task_id, execution_id


def test_applied_completion_binds_result_to_execution_and_task():
    manager, task_id, execution_id = make_manager(
        "completion-outcome"
    )

    transition = manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id=f"{execution_id}:completed",
        result="winning result",
    )

    task = manager.task_store.get(task_id)

    assert transition.execution.status == ExecutionStatus.COMPLETED
    assert transition.execution.result == "winning result"
    assert transition.execution.error is None
    assert task is not None
    assert task.status == "completed"
    assert task.result == "winning result"
    assert task.error is None


def test_idempotent_replay_cannot_replace_winning_result():
    manager, task_id, execution_id = make_manager(
        "completion-replay"
    )
    operation_id = f"{execution_id}:completed"

    manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id=operation_id,
        result="original winning result",
    )

    replay = manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id=operation_id,
        result="replacement result must not win",
    )

    task = manager.task_store.get(task_id)

    assert replay.disposition.value == "idempotent_replay"
    assert replay.execution.result == "original winning result"
    assert task is not None
    assert task.status == "completed"
    assert task.result == "original winning result"


def test_conflicting_attempt_restores_execution_winner_to_task():
    manager, task_id, execution_id = make_manager(
        "terminal-conflict"
    )

    manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id=f"{execution_id}:completed",
        result="winning result",
    )

    manager.task_store.update(
        task_id,
        status="running",
        error=None,
        result=None,
    )

    losing = manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id=f"{execution_id}:failed",
        error="losing error",
    )

    task = manager.task_store.get(task_id)

    assert (
        losing.disposition.value
        == "conflicting_terminal_attempt"
    )
    assert losing.execution.status == ExecutionStatus.COMPLETED
    assert losing.execution.result == "winning result"
    assert losing.execution.error is None
    assert task is not None
    assert task.status == "completed"
    assert task.result == "winning result"
    assert task.error is None


def test_failure_outcome_is_bound_and_protected():
    manager, task_id, execution_id = make_manager("failure-outcome")
    operation_id = f"{execution_id}:failed"

    accepted = manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id=operation_id,
        error="original winning error",
    )
    replay = manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id=operation_id,
        error="replacement error must not win",
    )
    task = manager.task_store.get(task_id)

    assert accepted.execution.error == "original winning error"
    assert replay.disposition.value == "idempotent_replay"
    assert replay.execution.error == "original winning error"
    assert replay.execution.result is None
    assert task is not None
    assert task.status == "failed"
    assert task.error == "original winning error"
    assert task.result is None

    with pytest.raises(ValueError, match="State changes require transition"):
        manager.execution_registry.save(
            replace(replay.execution, error="forged error")
        )


def test_stale_terminal_retry_preserves_error(monkeypatch):
    from core.work.execution_registry_contract import (
        TransitionDisposition,
        TransitionResult,
    )

    manager, task_id, execution_id = make_manager(
        "stale-terminal-payload"
    )
    original_transition = manager._transition_execution
    attempts = 0

    def stale_once(
        current_execution_id,
        *,
        target_status,
        operation_id,
        error=None,
        result=None,
    ):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            current = manager.execution_registry.get(
                current_execution_id
            )
            assert current is not None
            return TransitionResult(
                applied=False,
                disposition=TransitionDisposition.STALE_VERSION,
                execution=current,
            )

        return original_transition(
            current_execution_id,
            target_status=target_status,
            operation_id=operation_id,
            error=error,
            result=result,
        )

    monkeypatch.setattr(
        manager,
        "_transition_execution",
        stale_once,
    )

    transition = manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id=f"{execution_id}:failed",
        error="expected winning error",
    )

    task = manager.task_store.get(task_id)

    assert attempts == 2
    assert transition.execution.status == ExecutionStatus.FAILED
    assert transition.execution.error == "expected winning error"
    assert task is not None
    assert task.error == "expected winning error"
