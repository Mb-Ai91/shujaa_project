from __future__ import annotations

from typing import Protocol

from core.agents.executor_contract import AgentExecutorProtocol


class AgentExecutorRegistryProtocol(Protocol):
    """عقد الوصول إلى منفذات الوكلاء داخل شجاع."""

    def get(
        self,
        agent_id: str,
    ) -> AgentExecutorProtocol | None:
        ...
