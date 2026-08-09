from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_work_id() -> str:
    return f"work-{uuid4()}"


def new_execution_id() -> str:
    return f"exec-{uuid4()}"


class WorkStatus(StrEnum):
    QUEUED = "queued"
    PENDING_APPROVAL = "pending_approval"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Work:
    work_id: str
    request: str
    status: WorkStatus = WorkStatus.QUEUED
    priority: int = 0
    progress: float = 0.0
    queue_position: int | None = None
    parent_work_id: str | None = None
    dependency_work_ids: tuple[str, ...] = ()
    result: str | None = None
    artifact_refs: tuple[str, ...] = ()
    deadline_at: datetime | None = None
    sla_seconds: int | None = None
    event_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class Execution:
    execution_id: str
    work_id: str
    task_id: str
    status: ExecutionStatus = ExecutionStatus.QUEUED
    executor_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
