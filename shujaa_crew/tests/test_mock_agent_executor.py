import pytest

from adapters.agents.mock_executor import MockAgentExecutor
from core.agents.models import AgentDefinition


def build_agent() -> AgentDefinition:
    return AgentDefinition(
        agent_id="test-agent",
        name="Test Agent",
        description="Temporary test agent.",
        capabilities=("test",),
    )


def test_mock_agent_executor_returns_result():
    executor = MockAgentExecutor()

    result = executor.execute(
        build_agent(),
        "perform test",
    )

    assert result == (
        "Mock execution completed by "
        "test-agent: perform test"
    )


def test_mock_agent_executor_rejects_empty_task():
    executor = MockAgentExecutor()

    with pytest.raises(ValueError):
        executor.execute(
            build_agent(),
            "   ",
        )
