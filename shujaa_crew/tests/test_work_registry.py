from dataclasses import replace

import pytest

from core.work.models import (
    Work,
    WorkStatus,
    new_work_id,
)
from core.work.registry import InMemoryWorkRegistry


def test_registry_creates_and_gets_work():
    registry = InMemoryWorkRegistry()

    work = Work(
        work_id=new_work_id(),
        request="Test work.",
    )

    registry.create(work)

    assert registry.get(work.work_id) == work


def test_registry_rejects_duplicate_work_id():
    registry = InMemoryWorkRegistry()

    work = Work(
        work_id=new_work_id(),
        request="Original.",
    )

    registry.create(work)

    with pytest.raises(ValueError):
        registry.create(work)


def test_registry_saves_updated_work():
    registry = InMemoryWorkRegistry()

    work = Work(
        work_id=new_work_id(),
        request="Update lifecycle.",
    )

    registry.create(work)

    updated = replace(
        work,
        status=WorkStatus.RUNNING,
    )

    registry.save(updated)

    stored = registry.get(work.work_id)

    assert stored is not None
    assert stored.status == WorkStatus.RUNNING


def test_registry_rejects_save_for_unknown_work():
    registry = InMemoryWorkRegistry()

    work = Work(
        work_id=new_work_id(),
        request="Unknown work.",
    )

    with pytest.raises(ValueError):
        registry.save(work)


def test_registry_lists_registered_work():
    registry = InMemoryWorkRegistry()

    first = Work(
        work_id=new_work_id(),
        request="First.",
    )
    second = Work(
        work_id=new_work_id(),
        request="Second.",
    )

    registry.create(first)
    registry.create(second)

    assert registry.list() == [first, second]


def test_registry_finds_children():
    registry = InMemoryWorkRegistry()

    parent = Work(
        work_id=new_work_id(),
        request="Parent.",
    )
    child = Work(
        work_id=new_work_id(),
        request="Child.",
        parent_work_id=parent.work_id,
    )
    unrelated = Work(
        work_id=new_work_id(),
        request="Unrelated.",
    )

    registry.create(parent)
    registry.create(child)
    registry.create(unrelated)

    assert registry.find_children(parent.work_id) == [child]


def test_registry_dependencies_satisfied_without_dependencies():
    registry = InMemoryWorkRegistry()

    work = Work(
        work_id=new_work_id(),
        request="Independent.",
    )

    registry.create(work)

    assert registry.dependencies_satisfied(work) is True


def test_registry_dependencies_fail_when_missing():
    registry = InMemoryWorkRegistry()

    work = Work(
        work_id=new_work_id(),
        request="Missing dependency.",
        dependency_work_ids=("work-missing",),
    )

    registry.create(work)

    assert registry.dependencies_satisfied(work) is False


def test_registry_dependencies_fail_when_not_completed():
    registry = InMemoryWorkRegistry()

    dependency = Work(
        work_id=new_work_id(),
        request="Dependency.",
        status=WorkStatus.RUNNING,
    )
    dependent = Work(
        work_id=new_work_id(),
        request="Dependent.",
        dependency_work_ids=(dependency.work_id,),
    )

    registry.create(dependency)
    registry.create(dependent)

    assert registry.dependencies_satisfied(dependent) is False


def test_registry_dependencies_succeed_when_completed():
    registry = InMemoryWorkRegistry()

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
