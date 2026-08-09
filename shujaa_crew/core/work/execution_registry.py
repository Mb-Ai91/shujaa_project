from __future__ import annotations

from threading import Lock

from core.work.models import Execution


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

    def save(self, execution: Execution) -> None:
        with self._lock:
            if execution.execution_id not in self._executions:
                raise ValueError(
                    f"Execution does not exist: "
                    f"{execution.execution_id}"
                )

            self._executions[execution.execution_id] = execution
