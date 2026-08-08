from __future__ import annotations

from threading import Lock

from core.agents.models import AgentDefinition


class InMemoryAgentRegistry:
    """سجل وكلاء بسيط داخل الذاكرة."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}
        self._lock = Lock()

    def register(self, agent: AgentDefinition) -> None:
        with self._lock:
            if agent.agent_id in self._agents:
                raise ValueError(
                    f"Agent already registered: {agent.agent_id}"
                )

            self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> AgentDefinition | None:
        with self._lock:
            return self._agents.get(agent_id)

    def list(self) -> list[AgentDefinition]:
        with self._lock:
            return list(self._agents.values())

    def find_by_capability(
        self,
        capability: str,
    ) -> list[AgentDefinition]:
        normalized = capability.strip().lower()

        with self._lock:
            return [
                agent
                for agent in self._agents.values()
                if agent.enabled
                and normalized
                in {
                    item.strip().lower()
                    for item in agent.capabilities
                }
            ]
