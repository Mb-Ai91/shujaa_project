from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import Lock

from core.runtime.process_registry_contract import (
    ProcessOwnership,
    ProcessRegistryCorruptionError,
    RegistrationDisposition,
    RegistrationResult,
    ReleaseDisposition,
    ReleaseResult,
)

_LOCKS_GUARD = Lock()
_PATH_LOCKS: dict[str, Lock] = {}


class ProcessRegistry:
    """Local registry for process ownership held by Shujaa."""

    def __init__(self, path: Path | None = None) -> None:
        project_dir = Path(__file__).resolve().parents[2]
        self.path = path or project_dir / ".runtime" / "processes.json"
        self.path = self.path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)

        path_key = str(self.path)

        with _LOCKS_GUARD:
            self._lock = _PATH_LOCKS.setdefault(
                path_key,
                Lock(),
            )

    def _read(self) -> dict[str, ProcessOwnership]:
        if not self.path.exists():
            return {}

        try:
            raw_data = json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as error:
            raise ProcessRegistryCorruptionError(
                "Process registry contains invalid JSON."
            ) from error

        if not isinstance(raw_data, dict):
            raise ProcessRegistryCorruptionError(
                "Process registry root must be an object."
            )

        ownerships: dict[str, ProcessOwnership] = {}

        for task_id, raw_owner in raw_data.items():
            if not isinstance(task_id, str):
                raise ProcessRegistryCorruptionError(
                    "Process registry task id must be a string."
                )

            if not isinstance(raw_owner, dict):
                raise ProcessRegistryCorruptionError(
                    f"Invalid ownership record for {task_id}."
                )

            execution_id = raw_owner.get(
                "execution_id"
            )
            pid = raw_owner.get("pid")
            pgid = raw_owner.get("pgid")
            start_time = raw_owner.get(
                "process_start_time_ticks"
            )

            if (
                not isinstance(execution_id, str)
                or type(pid) is not int
                or type(pgid) is not int
                or (
                    start_time is not None
                    and type(start_time) is not int
                )
            ):
                raise ProcessRegistryCorruptionError(
                    f"Invalid ownership fields for {task_id}."
                )

            try:
                ownership = ProcessOwnership(
                    task_id=task_id,
                    execution_id=execution_id,
                    pid=pid,
                    pgid=pgid,
                    process_start_time_ticks=start_time,
                )
            except ValueError as error:
                raise ProcessRegistryCorruptionError(
                    f"Invalid ownership fields for {task_id}."
                ) from error

            ownerships[task_id] = ownership

        return ownerships

    def _write(
        self,
        ownerships: dict[str, ProcessOwnership],
    ) -> None:
        payload = {
            task_id: {
                "execution_id": ownership.execution_id,
                "pid": ownership.pid,
                "pgid": ownership.pgid,
                "process_start_time_ticks": (
                    ownership.process_start_time_ticks
                ),
            }
            for task_id, ownership in ownerships.items()
        }

        file_descriptor, temp_name = tempfile.mkstemp(
            prefix="processes-",
            suffix=".tmp",
            dir=self.path.parent,
        )
        temp_path = Path(temp_name)

        try:
            with os.fdopen(
                file_descriptor,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(payload, file, indent=2)

            os.replace(temp_path, self.path)
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    def register(
        self,
        ownership: ProcessOwnership,
    ) -> RegistrationResult:
        with self._lock:
            ownerships = self._read()
            existing = ownerships.get(ownership.task_id)

            if existing == ownership:
                return RegistrationResult(
                    disposition=(
                        RegistrationDisposition.IDEMPOTENT_REPLAY
                    ),
                    ownership=existing,
                )

            if existing is not None:
                return RegistrationResult(
                    disposition=(
                        RegistrationDisposition.OWNER_CONFLICT
                    ),
                    ownership=existing,
                )

            ownerships[ownership.task_id] = ownership
            self._write(ownerships)

            return RegistrationResult(
                disposition=RegistrationDisposition.REGISTERED,
                ownership=ownership,
            )

    def get(
        self,
        task_id: str,
    ) -> ProcessOwnership | None:
        with self._lock:
            return self._read().get(task_id)

    def release(
        self,
        task_id: str,
        *,
        expected_execution_id: str,
    ) -> ReleaseResult:
        with self._lock:
            ownerships = self._read()
            existing = ownerships.get(task_id)

            if existing is None:
                return ReleaseResult(
                    disposition=ReleaseDisposition.NOT_FOUND,
                    ownership=None,
                )

            if existing.execution_id != expected_execution_id:
                return ReleaseResult(
                    disposition=(
                        ReleaseDisposition.OWNER_MISMATCH
                    ),
                    ownership=existing,
                )

            ownerships.pop(task_id)
            self._write(ownerships)

            return ReleaseResult(
                disposition=ReleaseDisposition.RELEASED,
                ownership=existing,
            )

    def all(self) -> dict[str, ProcessOwnership]:
        with self._lock:
            return self._read()
