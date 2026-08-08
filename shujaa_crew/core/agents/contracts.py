from __future__ import annotations

from typing import Protocol

from core.agents.models import AgentDefinition


class AgentRegistryProtocol(Protocol):
    """العقد الذي يجب أن يطبقه أي سجل للوكلاء."""

    def register(self, agent: AgentDefinition) -> None:
        ...

    def get(self, agent_id: str) -> AgentDefinition | None:
        ...

    def list(self) -> list[AgentDefinition]:
        ...

    def find_by_capability(
        self,
        capability: str,
    ) -> list[AgentDefinition]:
        ...
