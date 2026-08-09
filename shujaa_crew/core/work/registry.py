from __future__ import annotations

from threading import Lock

from core.work.models import Work


class InMemoryWorkRegistry:
    """سجل أعمال مؤقت وآمن داخل العملية."""

    def __init__(self) -> None:
        self._works: dict[str, Work] = {}
        self._lock = Lock()

    def create(self, work: Work) -> None:
        with self._lock:
            if work.work_id in self._works:
                raise ValueError(
                    f"Work already exists: {work.work_id}"
                )

            self._works[work.work_id] = work

    def get(self, work_id: str) -> Work | None:
        with self._lock:
            return self._works.get(work_id)

    def list(self) -> list[Work]:
        with self._lock:
            return list(self._works.values())

    def save(self, work: Work) -> None:
        with self._lock:
            if work.work_id not in self._works:
                raise ValueError(
                    f"Work does not exist: {work.work_id}"
                )

            self._works[work.work_id] = work

    def find_children(
        self,
        parent_work_id: str,
    ) -> list[Work]:
        with self._lock:
            return [
                work
                for work in self._works.values()
                if work.parent_work_id == parent_work_id
            ]

    def dependencies_satisfied(
        self,
        work: Work,
    ) -> bool:
        from core.work.models import WorkStatus

        with self._lock:
            for dependency_id in work.dependency_work_ids:
                dependency = self._works.get(dependency_id)

                if dependency is None:
                    return False

                if dependency.status != WorkStatus.COMPLETED:
                    return False

            return True
