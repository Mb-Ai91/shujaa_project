from __future__ import annotations

from typing import Protocol

from core.work.models import Work


class WorkRegistryProtocol(Protocol):
    """عقد سجل الأعمال داخل شجاع."""

    def create(self, work: Work) -> None:
        ...

    def get(self, work_id: str) -> Work | None:
        ...

    def list(self) -> list[Work]:
        ...

    def save(self, work: Work) -> None:
        ...

    def find_children(
        self,
        parent_work_id: str,
    ) -> list[Work]:
        ...

    def dependencies_satisfied(
        self,
        work: Work,
    ) -> bool:
        ...
