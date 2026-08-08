import pytest

from core.agents.executor_registry import AgentExecutorRegistry
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


def build_service(
    agent: AgentDefinition | None = None,
) -> AgentService:
    registry = InMemoryAgentRegistry()
    executor_registry = AgentExecutorRegistry()

    if agent is not None:
        registry.register(agent)
        executor_registry.register(
            agent.agent_id,
            FakeExecutor(),
        )

    return AgentService(
        registry=registry,
        executor_registry=executor_registry,
    )


def test_agent_service_executes_agent_by_id():
    service = build_service(
        AgentDefinition(
            agent_id="research-agent",
            name="Research Agent",
            description="Researches information.",
            capabilities=("research",),
        )
    )

    result = service.execute_by_id(
        "research-agent",
        "test task",
    )

    assert result == "research-agent:test task"


def test_agent_service_executes_by_capability():
    service = build_service(
        AgentDefinition(
            agent_id="analysis-agent",
            name="Analysis Agent",
            description="Analyzes information.",
            capabilities=("analysis",),
        )
    )

    result = service.execute_by_capability(
        "analysis",
        "analyze this",
    )

    assert result == "analysis-agent:analyze this"


def test_agent_service_rejects_unknown_agent():
    service = build_service()

    with pytest.raises(ValueError):
        service.execute_by_id(
            "missing-agent",
            "test task",
        )


def test_agent_service_rejects_missing_executor():
    registry = InMemoryAgentRegistry()
    registry.register(
        AgentDefinition(
            agent_id="agent-without-executor",
            name="Agent",
            description="No executor.",
            capabilities=("test",),
        )
    )

    service = AgentService(
        registry=registry,
        executor_registry=AgentExecutorRegistry(),
    )

    with pytest.raises(ValueError):
        service.execute_by_id(
            "agent-without-executor",
            "test task",
        )
