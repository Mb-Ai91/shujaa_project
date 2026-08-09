from __future__ import annotations

from typing import Protocol


class WorkQueueProtocol(Protocol):
    """عقد طابور الأعمال المنتظرة داخل شجاع."""

    def enqueue(
        self,
        work_id: str,
        *,
        priority: int = 0,
    ) -> None:
        ...

    def dequeue(self) -> str | None:
        ...

    def peek(self) -> str | None:
        ...

    def remove(self, work_id: str) -> bool:
        ...

    def contains(self, work_id: str) -> bool:
        ...

    def list(self) -> list[str]:
        ...

    def __len__(self) -> int:
        ...
