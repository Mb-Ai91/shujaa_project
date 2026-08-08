import pytest

from core.agents.models import AgentDefinition
from core.agents.registry import InMemoryAgentRegistry


def test_agent_registry_registers_and_retrieves_agent():
    registry = InMemoryAgentRegistry()

    agent = AgentDefinition(
        agent_id="research-agent",
        name="Research Agent",
        description="Researches information.",
        capabilities=("research", "analysis"),
    )

    registry.register(agent)

    assert registry.get("research-agent") == agent


def test_agent_registry_finds_enabled_agents_by_capability():
    registry = InMemoryAgentRegistry()

    registry.register(
        AgentDefinition(
            agent_id="research-agent",
            name="Research Agent",
            description="Researches information.",
            capabilities=("research", "analysis"),
        )
    )

    registry.register(
        AgentDefinition(
            agent_id="disabled-agent",
            name="Disabled Agent",
            description="Disabled test agent.",
            capabilities=("research",),
            enabled=False,
        )
    )

    matches = registry.find_by_capability("RESEARCH")

    assert [agent.agent_id for agent in matches] == [
        "research-agent"
    ]


def test_agent_registry_rejects_duplicate_agent_id():
    registry = InMemoryAgentRegistry()

    agent = AgentDefinition(
        agent_id="agent-1",
        name="Agent",
        description="Test agent.",
        capabilities=("test",),
    )

    registry.register(agent)

    with pytest.raises(ValueError):
        registry.register(agent)
