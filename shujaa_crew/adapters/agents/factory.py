from __future__ import annotations

from core.agents.executor_contract import AgentExecutorProtocol
from core.agents.models import AgentDefinition
from adapters.agents.crewai_executor import CrewAIAgentExecutor
from adapters.agents.mock_executor import MockAgentExecutor


def build_agent_executor(
    agent: AgentDefinition,
) -> AgentExecutorProtocol:
    """يبني المنفّذ المناسب حسب إعداد الوكيل."""

    executor_name = agent.executor.strip().lower()

    if executor_name == "mock":
        return MockAgentExecutor()

    if executor_name == "crewai":
        return CrewAIAgentExecutor()

    raise ValueError(
        f"Unsupported agent executor: {executor_name}"
    )
