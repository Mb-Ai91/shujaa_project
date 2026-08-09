from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class _QueueItem:
    work_id: str
    priority: int
    sequence: int


class InMemoryWorkQueue:
    """طابور أعمال داخل الذاكرة مع أولوية مستقرة."""

    def __init__(self) -> None:
        self._items: list[_QueueItem] = []
        self._sequence = 0
        self._lock = Lock()

    def enqueue(
        self,
        work_id: str,
        *,
        priority: int = 0,
    ) -> None:
        with self._lock:
            if any(
                item.work_id == work_id
                for item in self._items
            ):
                raise ValueError(
                    f"Work already queued: {work_id}"
                )

            item = _QueueItem(
                work_id=work_id,
                priority=priority,
                sequence=self._sequence,
            )
            self._sequence += 1
            self._items.append(item)
            self._items.sort(
                key=lambda current: (
                    -current.priority,
                    current.sequence,
                )
            )

    def dequeue(self) -> str | None:
        with self._lock:
            if not self._items:
                return None

            return self._items.pop(0).work_id

    def peek(self) -> str | None:
        with self._lock:
            if not self._items:
                return None

            return self._items[0].work_id

    def remove(self, work_id: str) -> bool:
        with self._lock:
            for index, item in enumerate(self._items):
                if item.work_id == work_id:
                    self._items.pop(index)
                    return True

            return False

    def contains(self, work_id: str) -> bool:
        with self._lock:
            return any(
                item.work_id == work_id
                for item in self._items
            )

    def list(self) -> list[str]:
        with self._lock:
            return [
                item.work_id
                for item in self._items
            ]

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
