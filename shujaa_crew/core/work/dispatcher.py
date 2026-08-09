from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


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
