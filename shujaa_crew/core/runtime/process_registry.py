from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import Lock

_LOCKS_GUARD = Lock()
_PATH_LOCKS: dict[str, Lock] = {}


class ProcessRegistry:
    """سجل محلي للعمليات التي أنشأها شجاع فقط."""

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

    def _read(self) -> dict[str, dict[str, int]]:
        if not self.path.exists():
            return {}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

        return data if isinstance(data, dict) else {}

    def _write(self, data: dict[str, dict[str, int]]) -> None:
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
                json.dump(data, file, indent=2)

            os.replace(temp_path, self.path)
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    def register(self, task_id: str, pid: int, pgid: int) -> None:
        with self._lock:
            data = self._read()
            data[task_id] = {
                "pid": pid,
                "pgid": pgid,
            }
            self._write(data)

    def remove(self, task_id: str) -> None:
        with self._lock:
            data = self._read()
            data.pop(task_id, None)
            self._write(data)

    def all(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return self._read()

    def clear(self) -> None:
        with self._lock:
            self._write({})
