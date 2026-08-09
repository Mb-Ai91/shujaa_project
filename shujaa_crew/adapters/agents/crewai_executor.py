from __future__ import annotations

from core.agents.models import AgentDefinition


class CrewAIAgentExecutor:
    """منفّذ وكلاء يعتمد على CrewAI دون ربطه بالمدير."""

    def execute(
        self,
        agent: AgentDefinition,
        task: str,
    ) -> str:
        raise NotImplementedError(
            "CrewAI agent execution is not wired yet."
        )
