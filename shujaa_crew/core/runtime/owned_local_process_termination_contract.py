from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from core.runtime.process_registry_contract import ProcessOwnership


@dataclass(frozen=True)
class OwnedLocalProcessTerminationCommand:
    ownership: ProcessOwnership


class OwnedLocalProcessTerminationDisposition(str, Enum):
    GRACEFUL_TERMINATION = "graceful_termination"
    FORCED_TERMINATION = "forced_termination"
    ALREADY_EXITED = "already_exited"
    IDENTITY_MISMATCH = "identity_mismatch"
    PROCESS_GROUP_MISMATCH = "process_group_mismatch"
    OWNERSHIP_VERIFICATION_FAILURE = (
        "ownership_verification_failure"
    )
    UNSUPPORTED_OPERATION = "unsupported_operation"
    TERMINATION_FAILURE = "termination_failure"
    OUTCOME_UNKNOWN = "outcome_unknown"


@dataclass(frozen=True)
class OwnedLocalProcessTerminationResult:
    disposition: OwnedLocalProcessTerminationDisposition


@runtime_checkable
class OwnedLocalProcessTerminationAdapterProtocol(Protocol):
    def terminate(
        self,
        command: OwnedLocalProcessTerminationCommand,
    ) -> OwnedLocalProcessTerminationResult:
        ...
