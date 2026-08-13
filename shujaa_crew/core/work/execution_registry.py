from __future__ import annotations

from dataclasses import replace
from threading import Lock

from core.work.execution_registry_contract import (
    LosingObservation,
    TransitionDisposition,
    TransitionResult,
)
from core.work.models import Execution, ExecutionStatus


_TERMINAL_STATUSES = frozenset(
    {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMED_OUT,
        ExecutionStatus.CANCELLED,
    }
)


class InMemoryExecutionRegistry:
    """سجل محاولات التنفيذ داخل الذاكرة."""

    def __init__(self) -> None:
        self._executions: dict[str, Execution] = {}
        self._lock = Lock()

    def create(self, execution: Execution) -> None:
        with self._lock:
            if execution.execution_id in self._executions:
                raise ValueError(
                    f"Execution already exists: "
                    f"{execution.execution_id}"
                )

            self._executions[execution.execution_id] = execution

    def get(
        self,
        execution_id: str,
    ) -> Execution | None:
        with self._lock:
            return self._executions.get(execution_id)

    def list_by_task(
        self,
        task_id: str,
    ) -> list[Execution]:
        with self._lock:
            return [
                execution
                for execution in self._executions.values()
                if execution.task_id == task_id
            ]

    def transition(
        self,
        execution_id: str,
        *,
        target_status: ExecutionStatus,
        expected_version: int,
        operation_id: str,
        source: str,
    ) -> TransitionResult:
        """Commit a transition authorized by lifecycle authority."""
        with self._lock:
            execution = self._executions.get(execution_id)

            if execution is None:
                raise ValueError(
                    f"Execution does not exist: {execution_id}"
                )

            is_terminal = execution.status in _TERMINAL_STATUSES

            if (
                is_terminal
                and execution.status == target_status
                and execution.terminal_operation_id == operation_id
            ):
                return TransitionResult(
                    applied=False,
                    disposition=(
                        TransitionDisposition.IDEMPOTENT_REPLAY
                    ),
                    execution=execution,
                )

            if is_terminal:
                observation = LosingObservation(
                    operation_id=operation_id,
                    attempted_status=target_status,
                    source=source,
                    rejected_at_version=execution.state_version,
                )
                return TransitionResult(
                    applied=False,
                    disposition=(
                        TransitionDisposition
                        .CONFLICTING_TERMINAL_ATTEMPT
                    ),
                    execution=execution,
                    observation=observation,
                )

            if execution.state_version != expected_version:
                return TransitionResult(
                    applied=False,
                    disposition=TransitionDisposition.STALE_VERSION,
                    execution=execution,
                )

            updated = replace(
                execution,
                status=target_status,
                state_version=execution.state_version + 1,
                terminal_operation_id=(
                    operation_id
                    if target_status in _TERMINAL_STATUSES
                    else None
                ),
            )
            self._executions[execution_id] = updated

            return TransitionResult(
                applied=True,
                disposition=TransitionDisposition.APPLIED,
                execution=updated,
            )

    def save(self, execution: Execution) -> None:
        with self._lock:
            current = self._executions.get(
                execution.execution_id
            )

            if current is None:
                raise ValueError(
                    f"Execution does not exist: "
                    f"{execution.execution_id}"
                )

            protected_state_changed = (
                execution.status != current.status
                or (
                    execution.state_version
                    != current.state_version
                )
                or (
                    execution.terminal_operation_id
                    != current.terminal_operation_id
                )
            )

            if protected_state_changed:
                raise ValueError(
                    "State changes require transition."
                )

            self._executions[execution.execution_id] = execution
