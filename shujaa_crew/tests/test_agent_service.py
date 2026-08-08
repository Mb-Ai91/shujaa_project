import pytest

from core.agents.models import AgentDefinition
from core.agents.registry import InMemoryAgentRegistry
from core.agents.service import AgentService


class FakeExecutor:
    def execute(
        self,
        agent: AgentDefinition,
        task: str,
    ) -> str:
        return f"{agent.agent_id}:{task}"


def test_agent_service_executes_agent_by_id():
    registry = InMemoryAgentRegistry()
    registry.register(
        AgentDefinition(
            agent_id="research-agent",
            name="Research Agent",
            description="Researches information.",
            capabilities=("research",),
        )
    )

    service = AgentService(
        registry=registry,
        executor=FakeExecutor(),
    )

    result = service.execute_by_id(
        "research-agent",
        "test task",
    )

    assert result == "research-agent:test task"


def test_agent_service_executes_by_capability():
    registry = InMemoryAgentRegistry()
    registry.register(
        AgentDefinition(
            agent_id="analysis-agent",
            name="Analysis Agent",
            description="Analyzes information.",
            capabilities=("analysis",),
        )
    )

    service = AgentService(
        registry=registry,
        executor=FakeExecutor(),
    )

    result = service.execute_by_capability(
        "analysis",
        "analyze this",
    )

    assert result == "analysis-agent:analyze this"


def test_agent_service_rejects_unknown_agent():
    service = AgentService(
        registry=InMemoryAgentRegistry(),
        executor=FakeExecutor(),
    )

    with pytest.raises(ValueError):
        service.execute_by_id(
            "missing-agent",
            "test task",
        )
