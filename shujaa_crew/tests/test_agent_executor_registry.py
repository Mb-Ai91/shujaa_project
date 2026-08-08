import pytest

from core.agents.executor_registry import AgentExecutorRegistry
from core.agents.models import AgentDefinition


class FakeExecutor:
    def execute(
        self,
        agent: AgentDefinition,
        task: str,
    ) -> str:
        return task


def test_executor_registry_registers_and_retrieves_executor():
    registry = AgentExecutorRegistry()
    executor = FakeExecutor()

    registry.register("research-agent", executor)

    assert registry.get("research-agent") is executor


def test_executor_registry_rejects_duplicate_agent_id():
    registry = AgentExecutorRegistry()

    registry.register(
        "research-agent",
        FakeExecutor(),
    )

    with pytest.raises(ValueError):
        registry.register(
            "research-agent",
            FakeExecutor(),
        )


def test_executor_registry_returns_none_for_unknown_agent():
    registry = AgentExecutorRegistry()

    assert registry.get("missing-agent") is None
