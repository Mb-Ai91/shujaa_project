from dataclasses import replace

import pytest

from core.work.execution_registry import (
    InMemoryExecutionRegistry,
)
from core.work.models import (
    Execution,
    ExecutionStatus,
    new_execution_id,
)


def test_execution_registry_creates_and_gets_execution():
    registry = InMemoryExecutionRegistry()

    execution = Execution(
        execution_id=new_execution_id(),
        work_id="work-1",
        task_id="task-1",
    )

    registry.create(execution)

    assert registry.get(execution.execution_id) == execution


def test_execution_registry_rejects_duplicate_execution():
    registry = InMemoryExecutionRegistry()

    execution = Execution(
        execution_id=new_execution_id(),
        work_id="work-1",
        task_id="task-1",
    )

    registry.create(execution)

    with pytest.raises(ValueError):
        registry.create(execution)


def test_execution_registry_lists_attempts_by_task():
    registry = InMemoryExecutionRegistry()

    first = Execution(
        execution_id=new_execution_id(),
        work_id="work-1",
        task_id="task-1",
    )
    second = Execution(
        execution_id=new_execution_id(),
        work_id="work-1",
        task_id="task-1",
    )
    unrelated = Execution(
        execution_id=new_execution_id(),
        work_id="work-2",
        task_id="task-2",
    )

    registry.create(first)
    registry.create(second)
    registry.create(unrelated)

    assert registry.list_by_task("task-1") == [
        first,
        second,
    ]


def test_execution_registry_saves_updated_execution():
    registry = InMemoryExecutionRegistry()

    execution = Execution(
        execution_id=new_execution_id(),
        work_id="work-1",
        task_id="task-1",
    )

    registry.create(execution)

    updated = replace(
        execution,
        status=ExecutionStatus.RUNNING,
        executor_id="runner-default",
    )

    registry.save(updated)

    stored = registry.get(execution.execution_id)

    assert stored is not None
    assert stored.status == ExecutionStatus.RUNNING
    assert stored.executor_id == "runner-default"


def test_execution_registry_rejects_unknown_save():
    registry = InMemoryExecutionRegistry()

    execution = Execution(
        execution_id=new_execution_id(),
        work_id="work-1",
        task_id="task-1",
    )

    with pytest.raises(ValueError):
        registry.save(execution)
