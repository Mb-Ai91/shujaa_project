from __future__ import annotations

from threading import Event, Thread
from uuid import uuid4

from adapters.crewai.runner import CrewAIRunner
from core.tasks.store import TaskRecord, TaskStore


class ShujaaManager:
    """المدير المركزي لاستقبال المهام ومتابعة حالتها."""

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
                status="queued",
            )
        )

        started = Event()

        Thread(
            target=self._execute_task,
            args=(task_id, command, started),
            daemon=True,
        ).start()

        # انتظار قصير فقط لمساعدة الاختبارات، دون تعطيل طلب n8n.
        started.wait(timeout=0.1)

        task = self.task_store.get(task_id)

        return {
            "status": "accepted",
            "task_id": task_id,
            "process_id": task.process_id if task else None,
            "message": "Shujaa accepted the task.",
        }

    def get_task(self, task_id: str) -> dict[str, object] | None:
        task = self.task_store.get(task_id)
        return task.to_dict() if task else None

    def _execute_task(
        self,
        task_id: str,
        command: str,
        started: Event,
    ) -> None:
        try:
            process = self.crew_runner.start(command)

            self.task_store.update(
                task_id,
                status="running",
                process_id=process.pid,
            )

            started.set()

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
            started.set()
