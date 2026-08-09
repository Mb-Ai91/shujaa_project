from core.agents.executor_registry import AgentExecutorRegistry
from core.agents.executor_registry_contract import (
    AgentExecutorRegistryProtocol,
)
from core.agents.models import AgentDefinition


class FakeExecutor:
    def execute(
        self,
        agent: AgentDefinition,
        task: str,
    ) -> str:
        return f"{agent.agent_id}:{task}"


def test_agent_executor_registry_matches_contract():
    concrete_registry = AgentExecutorRegistry()
    executor = FakeExecutor()

    concrete_registry.register("agent-1", executor)

    registry: AgentExecutorRegistryProtocol = concrete_registry

    assert registry.get("agent-1") is executor
