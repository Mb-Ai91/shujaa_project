from __future__ import annotations

import os
import signal
import time

from core.runtime.owned_local_process_termination_contract import (
    OwnedLocalProcessTerminationCommand,
    OwnedLocalProcessTerminationDisposition,
    OwnedLocalProcessTerminationResult,
)


class LocalProcessTerminationAdapter:
    """Technical adapter for one verified local process generation."""

    def __init__(self, *, grace_period_seconds: float = 5) -> None:
        if grace_period_seconds < 0:
            raise ValueError(
                "grace_period_seconds must be non-negative."
            )
        self.grace_period_seconds = grace_period_seconds

    @staticmethod
    def _read_process_start_time_ticks(pid: int) -> int | None:
        try:
            with open(
                f"/proc/{pid}/stat",
                encoding="utf-8",
            ) as file:
                stat = file.read()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise RuntimeError(
                "Unable to read local process identity."
            ) from error

        closing_parenthesis = stat.rfind(")")
        if closing_parenthesis < 0:
            raise RuntimeError("Malformed local process identity.")

        remaining_fields = stat[closing_parenthesis + 1:].split()
        if len(remaining_fields) <= 19:
            raise RuntimeError("Malformed local process identity.")

        try:
            start_time = int(remaining_fields[19])
        except ValueError as error:
            raise RuntimeError(
                "Malformed local process identity."
            ) from error

        if start_time <= 0:
            raise RuntimeError("Invalid local process identity.")
        return start_time

    @staticmethod
    def _result(
        disposition: OwnedLocalProcessTerminationDisposition,
    ) -> OwnedLocalProcessTerminationResult:
        return OwnedLocalProcessTerminationResult(
            disposition=disposition
        )

    @staticmethod
    def _wait_for_exit(pgid: int, timeout: float) -> bool:
        deadline = time.monotonic() + timeout

        while True:
            try:
                os.killpg(pgid, 0)
            except ProcessLookupError:
                return True

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(0.05, remaining))

    def terminate(
        self,
        command: OwnedLocalProcessTerminationCommand,
    ) -> OwnedLocalProcessTerminationResult:
        if not isinstance(
            command,
            OwnedLocalProcessTerminationCommand,
        ):
            return self._result(
                OwnedLocalProcessTerminationDisposition
                .UNSUPPORTED_OPERATION
            )

        ownership = command.ownership
        try:
            current_start_time = self._read_process_start_time_ticks(
                ownership.pid
            )
        except Exception:
            return self._result(
                OwnedLocalProcessTerminationDisposition
                .OWNERSHIP_VERIFICATION_FAILURE
            )

        if current_start_time is None:
            return self._result(
                OwnedLocalProcessTerminationDisposition.ALREADY_EXITED
            )

        if (
            ownership.process_start_time_ticks is None
            or current_start_time
            != ownership.process_start_time_ticks
        ):
            return self._result(
                OwnedLocalProcessTerminationDisposition
                .IDENTITY_MISMATCH
            )

        try:
            current_pgid = os.getpgid(ownership.pid)
        except ProcessLookupError:
            return self._result(
                OwnedLocalProcessTerminationDisposition.ALREADY_EXITED
            )
        except Exception:
            return self._result(
                OwnedLocalProcessTerminationDisposition
                .OWNERSHIP_VERIFICATION_FAILURE
            )

        if current_pgid != ownership.pgid:
            return self._result(
                OwnedLocalProcessTerminationDisposition
                .PROCESS_GROUP_MISMATCH
            )

        try:
            os.killpg(ownership.pgid, signal.SIGTERM)
        except ProcessLookupError:
            return self._result(
                OwnedLocalProcessTerminationDisposition.ALREADY_EXITED
            )
        except Exception:
            return self._result(
                OwnedLocalProcessTerminationDisposition
                .TERMINATION_FAILURE
            )

        try:
            if self._wait_for_exit(
                ownership.pgid,
                self.grace_period_seconds,
            ):
                return self._result(
                    OwnedLocalProcessTerminationDisposition
                    .GRACEFUL_TERMINATION
                )

            os.killpg(ownership.pgid, signal.SIGKILL)
            if self._wait_for_exit(
                ownership.pgid,
                self.grace_period_seconds,
            ):
                return self._result(
                    OwnedLocalProcessTerminationDisposition
                    .FORCED_TERMINATION
                )
        except ProcessLookupError:
            return self._result(
                OwnedLocalProcessTerminationDisposition
                .FORCED_TERMINATION
            )
        except Exception:
            return self._result(
                OwnedLocalProcessTerminationDisposition.OUTCOME_UNKNOWN
            )

        return self._result(
            OwnedLocalProcessTerminationDisposition.TERMINATION_FAILURE
        )
