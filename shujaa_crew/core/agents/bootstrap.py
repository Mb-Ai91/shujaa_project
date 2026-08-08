from __future__ import annotations

from pathlib import Path

from core.agents.config_loader import AgentConfigLoader
from core.agents.registry import InMemoryAgentRegistry


def build_agent_registry(
    config_dir: str | Path,
) -> InMemoryAgentRegistry:
    """يبني سجل الوكلاء من ملفات الإعداد."""

    registry = InMemoryAgentRegistry()
    loader = AgentConfigLoader(config_dir)

    for agent in loader.load_all():
        registry.register(agent)

    return registry
