from __future__ import annotations

from typing import Protocol


class ProcessProtocol(Protocol):
    pid: int

    def wait(self, timeout: float | None = None) -> int:
        ...


class RunnerProtocol(Protocol):
    """العقد الذي يجب أن يطبقه أي مشغّل مهام."""

    def start(self, topic: str) -> ProcessProtocol:
        ...

    def get_error(self, return_code: int) -> str:
        ...
