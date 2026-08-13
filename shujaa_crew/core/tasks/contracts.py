from __future__ import annotations

from typing import Protocol

from core.tasks.store import UNSET, TaskRecord, UnsetValue


class TaskStoreProtocol(Protocol):
    """العقد الذي يجب أن تطبقه أي طبقة تخزين للمهام."""

    def create(self, task: TaskRecord) -> None:
        ...

    def get(self, task_id: str) -> TaskRecord | None:
        ...

    def update(
        self,
        task_id: str,
        *,
        status: str,
        process_id: int | None = None,
        process_group_id: int | None = None,
        error: str | None | UnsetValue = UNSET,
        result: str | None | UnsetValue = UNSET,
    ) -> None:
        ...
