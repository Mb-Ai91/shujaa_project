from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from core.agents.contracts import AgentRegistryProtocol


@dataclass(frozen=True)
class DispatchRequest:
    """طلب توجيه تنفيذ داخل شجاع."""

    work_id: str
    task_id: str
    execution_id: str
    command: str
    requested_agent_id: str | None = None
    required_capability: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DispatchDecision:
    """قرار توجيه مستقل عن إطار أو مشغّل محدد."""

    executor_id: str
    agent_id: str | None = None
    runtime_id: str | None = None
    workflow_id: str | None = None
    tool_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ExecutionDispatcherProtocol(Protocol):
    """عقد اختيار مسار التنفيذ دون تنفيذ العمل نفسه."""

    def dispatch(
        self,
        request: DispatchRequest,
    ) -> DispatchDecision:
        ...


class DefaultExecutionDispatcher:
    """موجّه افتراضي لمسارات التنفيذ داخل شجاع."""

    def __init__(
        self,
        executor_id: str = "runner-default",
        runtime_id: str = "process-runner",
        agent_registry: AgentRegistryProtocol | None = None,
    ) -> None:
        self.executor_id = executor_id
        self.runtime_id = runtime_id
        self.agent_registry = agent_registry

    def dispatch(
        self,
        request: DispatchRequest,
    ) -> DispatchDecision:
        if request.requested_agent_id is not None:
            if self.agent_registry is None:
                raise ValueError(
                    "Agent registry is required for agent routing."
                )

            agent = self.agent_registry.get(
                request.requested_agent_id
            )

            if agent is None:
                raise ValueError(
                    f"Agent not found: "
                    f"{request.requested_agent_id}"
                )

            if not agent.enabled:
                raise ValueError(
                    f"Agent is disabled: {agent.agent_id}"
                )

            return DispatchDecision(
                executor_id=agent.agent_id,
                agent_id=agent.agent_id,
                runtime_id="agent-executor",
                metadata={
                    "route": "agent-executor",
                    "executor_type": agent.executor,
                },
            )

        return DispatchDecision(
            executor_id=self.executor_id,
            runtime_id=self.runtime_id,
            metadata={
                "route": "default-runner",
            },
        )
