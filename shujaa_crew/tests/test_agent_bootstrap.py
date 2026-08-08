import json

from core.agents.bootstrap import build_agent_registry


def test_build_agent_registry_loads_configured_agents(tmp_path):
    config_dir = tmp_path / "agents"
    config_dir.mkdir()

    (config_dir / "agent.json").write_text(
        json.dumps(
            {
                "agent_id": "configured-agent",
                "name": "Configured Agent",
                "description": "Loaded from configuration.",
                "capabilities": ["analysis"],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    registry = build_agent_registry(config_dir)

    agent = registry.get("configured-agent")

    assert agent is not None
    assert agent.name == "Configured Agent"
    assert agent.capabilities == ("analysis",)
