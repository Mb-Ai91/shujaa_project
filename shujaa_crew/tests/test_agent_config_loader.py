import json

import pytest

from core.agents.config_loader import AgentConfigLoader


def test_agent_config_loader_loads_agents(tmp_path):
    config_dir = tmp_path / "agents"
    config_dir.mkdir()

    (config_dir / "agent.json").write_text(
        json.dumps(
            {
                "agent_id": "test-agent",
                "name": "Test Agent",
                "description": "Temporary test agent.",
                "capabilities": ["research", "analysis"],
                "enabled": True,
            }
        ),
        encoding="utf-8",
    )

    agents = AgentConfigLoader(config_dir).load_all()

    assert len(agents) == 1
    assert agents[0].agent_id == "test-agent"
    assert agents[0].capabilities == (
        "research",
        "analysis",
    )


def test_agent_config_loader_rejects_duplicate_ids(tmp_path):
    config_dir = tmp_path / "agents"
    config_dir.mkdir()

    data = {
        "agent_id": "duplicate-agent",
        "name": "Agent",
        "description": "Test.",
        "capabilities": ["test"],
    }

    for filename in ("one.json", "two.json"):
        (config_dir / filename).write_text(
            json.dumps(data),
            encoding="utf-8",
        )

    with pytest.raises(ValueError):
        AgentConfigLoader(config_dir).load_all()


def test_agent_config_loader_rejects_missing_fields(tmp_path):
    config_dir = tmp_path / "agents"
    config_dir.mkdir()

    (config_dir / "invalid.json").write_text(
        json.dumps(
            {
                "agent_id": "invalid-agent",
                "name": "Invalid Agent",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        AgentConfigLoader(config_dir).load_all()
