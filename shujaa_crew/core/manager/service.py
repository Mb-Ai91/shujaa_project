from __future__ import annotations

from threading import Thread
from uuid import uuid4

from adapters.crewai.runner import CrewAIRunner
from core.tasks.store import TaskRecord, TaskStore


class ShujaaManager:
    """الطبقة المركزية لاستقبال المهام ومتابعة حالتها."""

    MAX_COMMAND_LENGTH = 4000

    def __init__(
        self,
        crew_runner: CrewAIRunner | None = None,
        task_store: TaskStore | None = None,
    ) -> None:
        self.crew_runner = crew_runner or CrewAIRunner()
        self.task_store = task_store or TaskStore()

    def submit(self, command: object) -> dict[str, object]:
        if not isinstance(command, str):
            raise ValueError("Command must be a string.")

        command = command.strip()

        if not command:
            raise ValueError("Command is required.")

        if len(command) > self.MAX_COMMAND_LENGTH:
            raise ValueError("Command exceeds the allowed length.")

        task_id = str(uuid4())

        self.task_store.create(
            TaskRecord(
                task_id=task_id,
                command=command,
                status="starting",
            )
        )

        try:
            process = self.crew_runner.start(command)
        except Exception as error:
            self.task_store.update(
                task_id,
                status="failed",
                error=str(error),
            )
            raise RuntimeError("Unable to start task execution.") from error

        self.task_store.update(
            task_id,
            status="running",
            process_id=process.pid,
        )

        Thread(
            target=self._watch_process,
            args=(task_id, process),
            daemon=True,
        ).start()

        return {
            "status": "accepted",
            "task_id": task_id,
            "process_id": process.pid,
            "message": "Shujaa accepted the task.",
        }

    def get_task(self, task_id: str) -> dict[str, object] | None:
        task = self.task_store.get(task_id)
        return task.to_dict() if task else None

    def _watch_process(self, task_id: str, process: object) -> None:
        try:
            return_code = process.wait()

            self.task_store.update(
                task_id,
                status="completed" if return_code == 0 else "failed",
                error=None if return_code == 0 else f"Exit code: {return_code}",
            )
        except Exception as error:
            self.task_store.update(
                task_id,
                status="failed",
                error=str(error),
            )
