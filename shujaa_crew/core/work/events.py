from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.work.models import utc_now


def new_event_id() -> str:
    return f"event-{uuid4()}"


@dataclass(frozen=True)
class WorkEvent:
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    work_id: str | None = None
    task_id: str | None = None
    execution_id: str | None = None
    actor_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
