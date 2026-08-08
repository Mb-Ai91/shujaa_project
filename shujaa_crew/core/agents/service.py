from __future__ import annotations

from core.agents.contracts import AgentRegistryProtocol
from core.agents.executor_registry import AgentExecutorRegistry


class AgentService:
    """خدمة عامة لاختيار الوكلاء وتشغيلهم داخل شجاع."""

    def __init__(
        self,
        registry: AgentRegistryProtocol,
        executor_registry: AgentExecutorRegistry,
    ) -> None:
        self.registry = registry
        self.executor_registry = executor_registry

    def execute_by_id(
        self,
        agent_id: str,
        task: str,
    ) -> str:
        agent = self.registry.get(agent_id)

        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")

        if not agent.enabled:
            raise ValueError(f"Agent is disabled: {agent_id}")

        executor = self.executor_registry.get(agent.agent_id)

        if executor is None:
            raise ValueError(
                f"No executor registered for agent: {agent.agent_id}"
            )

        return executor.execute(agent, task)

    def execute_by_capability(
        self,
        capability: str,
        task: str,
    ) -> str:
        agents = self.registry.find_by_capability(capability)

        if not agents:
            raise ValueError(
                f"No enabled agent supports capability: {capability}"
            )

        for agent in agents:
            executor = self.executor_registry.get(agent.agent_id)

            if executor is not None:
                return executor.execute(agent, task)

        raise ValueError(
            f"No executor registered for capability: {capability}"
        )
