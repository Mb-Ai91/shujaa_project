from __future__ import annotations

from core.agents.models import AgentDefinition


class MockAgentExecutor:
    """منفّذ محلي للوكلاء لا يستخدم أي نموذج ذكاء اصطناعي."""

    def execute(
        self,
        agent: AgentDefinition,
        task: str,
    ) -> str:
        task = task.strip()

        if not task:
            raise ValueError("Task is required.")

        return (
            f"Mock execution completed by "
            f"{agent.agent_id}: {task}"
        )
