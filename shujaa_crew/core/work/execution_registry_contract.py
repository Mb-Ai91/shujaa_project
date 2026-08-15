from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from core.work.models import Execution, ExecutionStatus


class TransitionDisposition(StrEnum):
    APPLIED = "applied"
    STALE_VERSION = "stale_version"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    CONFLICTING_TERMINAL_ATTEMPT = (
        "conflicting_terminal_attempt"
    )


class RetryAdmissionDisposition(StrEnum):
    APPLIED = "applied"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    CONFLICTING_RETRY = "conflicting_retry"


@dataclass(frozen=True)
class RetryAdmissionResult:
    applied: bool
    disposition: RetryAdmissionDisposition
    execution: Execution


@dataclass(frozen=True)
class LosingObservation:
    operation_id: str
    attempted_status: ExecutionStatus
    source: str
    rejected_at_version: int


@dataclass(frozen=True)
class TransitionResult:
    applied: bool
    disposition: TransitionDisposition
    execution: Execution
    observation: LosingObservation | None = None


class ExecutionRegistryProtocol(Protocol):
    """عقد سجل محاولات التنفيذ داخل شجاع."""

    def create(self, execution: Execution) -> None:
        ...

    def get(
        self,
        execution_id: str,
    ) -> Execution | None:
        ...

    def list_by_task(
        self,
        task_id: str,
    ) -> list[Execution]:
        ...

    def admit_retry(
        self,
        source_execution_id: str,
        *,
        execution_id: str,
        operation_id: str,
        executor_id: str | None = None,
    ) -> RetryAdmissionResult:
        ...

    def transition(
        self,
        execution_id: str,
        *,
        target_status: ExecutionStatus,
        expected_version: int,
        operation_id: str,
        source: str,
        error: str | None = None,
        result: str | None = None,
    ) -> TransitionResult:
        ...

    def save(self, execution: Execution) -> None:
        ...
