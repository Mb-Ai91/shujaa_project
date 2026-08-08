from __future__ import annotations

from core.agents.contracts import AgentRegistryProtocol
from core.agents.executor_contract import AgentExecutorProtocol


class AgentService:
    """خدمة عامة لاختيار الوكلاء وتشغيلهم داخل شجاع."""

    def __init__(
        self,
        registry: AgentRegistryProtocol,
        executor: AgentExecutorProtocol,
    ) -> None:
        self.registry = registry
        self.executor = executor

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

        return self.executor.execute(agent, task)

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

        return self.executor.execute(agents[0], task)
