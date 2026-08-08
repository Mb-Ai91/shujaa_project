from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentDefinition:
    """تعريف منطقي لوكيل داخل شجاع، مستقل عن إطار التنفيذ."""

    agent_id: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    enabled: bool = True
