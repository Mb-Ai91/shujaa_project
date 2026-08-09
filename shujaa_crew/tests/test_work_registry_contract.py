from __future__ import annotations

from core.work.models import (
    Work,
    WorkStatus,
    new_work_id,
)
from core.work.registry_contract import WorkRegistryProtocol


class FakeWorkRegistry:
    def __init__(self) -> None:
        self.items: dict[str, Work] = {}

    def create(self, work: Work) -> None:
        self.items[work.work_id] = work

    def get(self, work_id: str) -> Work | None:
        return self.items.get(work_id)

    def list(self) -> list[Work]:
        return list(self.items.values())

    def save(self, work: Work) -> None:
        self.items[work.work_id] = work

    def find_children(
        self,
        parent_work_id: str,
    ) -> list[Work]:
        return [
            work
            for work in self.items.values()
            if work.parent_work_id == parent_work_id
        ]

    def dependencies_satisfied(
        self,
        work: Work,
    ) -> bool:
        for dependency_id in work.dependency_work_ids:
            dependency = self.items.get(dependency_id)

            if dependency is None:
                return False

            if dependency.status != WorkStatus.COMPLETED:
                return False

        return True


def test_work_registry_contract_supports_work_lifecycle():
    registry: WorkRegistryProtocol = FakeWorkRegistry()

    work = Work(
        work_id=new_work_id(),
        request="Test registry contract.",
    )

    registry.create(work)

    assert registry.get(work.work_id) == work
    assert registry.list() == [work]

    registry.save(work)

    assert registry.get(work.work_id) == work


def test_work_registry_contract_supports_parent_child_lookup():
    registry: WorkRegistryProtocol = FakeWorkRegistry()

    parent = Work(
        work_id=new_work_id(),
        request="Parent.",
    )
    child = Work(
        work_id=new_work_id(),
        request="Child.",
        parent_work_id=parent.work_id,
    )

    registry.create(parent)
    registry.create(child)

    assert registry.find_children(parent.work_id) == [child]


def test_work_registry_contract_supports_dependency_checks():
    registry: WorkRegistryProtocol = FakeWorkRegistry()

    dependency = Work(
        work_id=new_work_id(),
        request="Dependency.",
        status=WorkStatus.COMPLETED,
    )
    dependent = Work(
        work_id=new_work_id(),
        request="Dependent.",
        dependency_work_ids=(dependency.work_id,),
    )

    registry.create(dependency)
    registry.create(dependent)

    assert registry.dependencies_satisfied(dependent) is True
