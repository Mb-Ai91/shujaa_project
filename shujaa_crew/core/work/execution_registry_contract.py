from __future__ import annotations

from typing import Protocol

from core.work.models import Execution


class ExecutionRegistryProtocol(Protocol):
    """عقد سجل محاولات التنفيذ داخل شجاع."""

    def create(self, execution: Execution) -> None:
        ...

    def get(
        self,
        execution_id: str,
    ) -> Execution | None:
        ...

    def list_by_task(
        self,
        task_id: str,
    ) -> list[Execution]:
        ...

    def save(self, execution: Execution) -> None:
        ...
