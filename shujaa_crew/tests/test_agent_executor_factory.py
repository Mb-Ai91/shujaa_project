import pytest

from adapters.agents.crewai_executor import CrewAIAgentExecutor
from adapters.agents.factory import build_agent_executor
from adapters.agents.mock_executor import MockAgentExecutor
from core.agents.models import AgentDefinition


def build_agent(executor: str) -> AgentDefinition:
    return AgentDefinition(
        agent_id="test-agent",
        name="Test Agent",
        description="Test.",
        capabilities=("test",),
        executor=executor,
    )


def test_factory_builds_mock_executor():
    executor = build_agent_executor(
        build_agent("mock")
    )

    assert isinstance(executor, MockAgentExecutor)


def test_factory_rejects_unknown_executor():
    with pytest.raises(ValueError):
        build_agent_executor(
            build_agent("unknown")
        )


def test_factory_builds_crewai_executor():
    executor = build_agent_executor(
        build_agent("crewai")
    )

    assert isinstance(executor, CrewAIAgentExecutor)
