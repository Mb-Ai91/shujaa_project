from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class ProcessRegistryCorruptionError(RuntimeError):
    """The persisted ownership registry cannot be trusted."""


@dataclass(frozen=True)
class ProcessOwnership:
    task_id: str
    execution_id: str
    pid: int
    pgid: int
    process_start_time_ticks: int | None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.task_id, str)
            or not self.task_id.strip()
        ):
            raise ValueError("task_id must be non-empty.")

        if (
            not isinstance(self.execution_id, str)
            or not self.execution_id.strip()
        ):
            raise ValueError(
                "execution_id must be non-empty."
            )

        if type(self.pid) is not int or self.pid <= 0:
            raise ValueError("pid must be a positive integer.")

        if type(self.pgid) is not int or self.pgid <= 0:
            raise ValueError(
                "pgid must be a positive integer."
            )

        if (
            self.process_start_time_ticks is not None
            and (
                type(self.process_start_time_ticks) is not int
                or self.process_start_time_ticks <= 0
            )
        ):
            raise ValueError(
                "process_start_time_ticks must be positive."
            )


class RegistrationDisposition(str, Enum):
    REGISTERED = "registered"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    OWNER_CONFLICT = "owner_conflict"


@dataclass(frozen=True)
class RegistrationResult:
    disposition: RegistrationDisposition
    ownership: ProcessOwnership


class ReleaseDisposition(str, Enum):
    RELEASED = "released"
    NOT_FOUND = "not_found"
    OWNER_MISMATCH = "owner_mismatch"


@dataclass(frozen=True)
class ReleaseResult:
    disposition: ReleaseDisposition
    ownership: ProcessOwnership | None


class CleanupDisposition(str, Enum):
    TERMINATED_AND_RELEASED = "terminated_and_released"
    ALREADY_EXITED_AND_RELEASED = (
        "already_exited_and_released"
    )
    NOT_OWNED = "not_owned"
    OWNER_MISMATCH = "owner_mismatch"
    IDENTITY_MISMATCH = "identity_mismatch"
    PROCESS_GROUP_MISMATCH = "process_group_mismatch"
    IDENTITY_CHECK_FAILED_RETAINED = (
        "identity_check_failed_retained"
    )
    TERMINATION_FAILED_RETAINED = (
        "termination_failed_retained"
    )


@dataclass(frozen=True)
class CleanupResult:
    disposition: CleanupDisposition
    ownership: ProcessOwnership | None
    error: str | None = None


@runtime_checkable
class ProcessRegistryProtocol(Protocol):
    def register(
        self,
        ownership: ProcessOwnership,
    ) -> RegistrationResult:
        ...

    def get(
        self,
        task_id: str,
    ) -> ProcessOwnership | None:
        ...

    def release(
        self,
        task_id: str,
        *,
        expected_execution_id: str,
    ) -> ReleaseResult:
        ...

    def all(self) -> dict[str, ProcessOwnership]:
        ...
