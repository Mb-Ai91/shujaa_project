from __future__ import annotations

from typing import Protocol

from core.agents.models import AgentDefinition


class AgentExecutorProtocol(Protocol):
    """عقد تنفيذ وكيل منطقي داخل شجاع."""

    def execute(
        self,
        agent: AgentDefinition,
        task: str,
    ) -> str:
        ...
