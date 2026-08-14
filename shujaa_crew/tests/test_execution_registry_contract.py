from __future__ import annotations

import inspect

from core.work.execution_registry_contract import (
    ExecutionRegistryProtocol,
)
from core.work.models import (
    Execution,
    new_execution_id,
)


class FakeExecutionRegistry:
    def __init__(self) -> None:
        self.items: dict[str, Execution] = {}

    def create(self, execution: Execution) -> None:
        self.items[execution.execution_id] = execution

    def get(
        self,
        execution_id: str,
    ) -> Execution | None:
        return self.items.get(execution_id)

    def list_by_task(
        self,
        task_id: str,
    ) -> list[Execution]:
        return [
            execution
            for execution in self.items.values()
            if execution.task_id == task_id
        ]

    def save(self, execution: Execution) -> None:
        self.items[execution.execution_id] = execution


def test_execution_registry_supports_multiple_attempts_per_task():
    registry: ExecutionRegistryProtocol = (
        FakeExecutionRegistry()
    )

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

    registry.create(first)
    registry.create(second)

    executions = registry.list_by_task("task-1")

    assert executions == [first, second]
    assert registry.get(first.execution_id) == first


def test_execution_registry_protocol_declares_atomic_transition():
    transition = getattr(
        ExecutionRegistryProtocol,
        "transition",
        None,
    )

    assert callable(transition)

    signature = inspect.signature(transition)

    assert tuple(signature.parameters) == (
        "self",
        "execution_id",
        "target_status",
        "expected_version",
        "operation_id",
        "source",
        "error",
        "result",
    )

    for name in (
        "target_status",
        "expected_version",
        "operation_id",
        "source",
        "error",
        "result",
    ):
        assert (
            signature.parameters[name].kind
            is inspect.Parameter.KEYWORD_ONLY
        )
