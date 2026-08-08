from __future__ import annotations

import os
import signal
import subprocess
from threading import Event, Thread
from uuid import uuid4

from adapters.crewai.runner import CrewAIRunner
from core.runtime.process_registry import ProcessRegistry
from core.tasks.contracts import TaskStoreProtocol
from core.tasks.store import InMemoryTaskStore, TaskRecord


class ShujaaManager:
    """المدير المركزي لاستقبال المهام ومتابعة حالتها."""

    MAX_COMMAND_LENGTH = 4000
    TASK_TIMEOUT_SECONDS = 120
    TERMINATION_GRACE_SECONDS = 5

    def __init__(
        self,
        crew_runner: CrewAIRunner | None = None,
        task_store: TaskStoreProtocol | None = None,
        process_registry: ProcessRegistry | None = None,
    ) -> None:
        self.crew_runner = crew_runner or CrewAIRunner()
        self.task_store = task_store or InMemoryTaskStore()
        self.process_registry = process_registry or ProcessRegistry()

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

            try:
                process_group_id = os.getpgid(process.pid)
            except ProcessLookupError:
                # دعم العمليات الوهمية في الاختبارات.
                process_group_id = process.pid

            self.process_registry.register(
                task_id,
                process.pid,
                process_group_id,
            )

            self.task_store.update(
                task_id,
                status="running",
                process_id=process.pid,
                process_group_id=process_group_id,
            )

            started.set()

            try:
                return_code = process.wait(
                    timeout=self.TASK_TIMEOUT_SECONDS
                )
            except TypeError:
                # دعم المشغلات الوهمية في الاختبارات.
                return_code = process.wait()
            except subprocess.TimeoutExpired:
                self._terminate_process_group(
                    process,
                    process_group_id,
                )

                self.task_store.update(
                    task_id,
                    status="timed_out",
                    error=(
                        f"Task exceeded "
                        f"{self.TASK_TIMEOUT_SECONDS} seconds."
                    ),
                )
                self.process_registry.remove(task_id)
                return

            current_task = self.task_store.get(task_id)

            if current_task and current_task.status == "cancelled":
                self.process_registry.remove(task_id)
                return

            if return_code == 0:
                result = None
                result_reader = getattr(
                    self.crew_runner,
                    "get_result",
                    None,
                )

                if callable(result_reader):
                    result = result_reader(process)

                self.task_store.update(
                    task_id,
                    status="completed",
                    error=None,
                    result=result,
                )
            else:
                error_message = f"Exit code: {return_code}"

                try:
                    log_text = self.crew_runner.log_path.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                    recent_log = log_text[-12000:]

                    if (
                        "RESOURCE_EXHAUSTED" in recent_log
                        or "429" in recent_log
                    ):
                        error_message = (
                            "LLM quota exhausted: "
                            "RESOURCE_EXHAUSTED (429)."
                        )
                    else:
                        meaningful_lines = [
                            line.strip()
                            for line in recent_log.splitlines()
                            if line.strip()
                            and any(
                                keyword in line.lower()
                                for keyword in (
                                    "error",
                                    "failed",
                                    "exception",
                                    "missing required input",
                                    "connection reset",
                                    "socket hang up",
                                )
                            )
                        ]

                        if meaningful_lines:
                            error_message = meaningful_lines[-1][:500]

                except OSError:
                    pass

                self.task_store.update(
                    task_id,
                    status="failed",
                    error=error_message,
                )

            self.process_registry.remove(task_id)

        except Exception as error:
            self.task_store.update(
                task_id,
                status="failed",
                error=str(error),
            )
            started.set()

    def cancel_task(self, task_id: str) -> dict[str, object]:
        task = self.task_store.get(task_id)

        if task is None:
            raise ValueError("Task not found.")

        if task.status not in {"queued", "running"}:
            raise ValueError("Task is not cancellable.")

        self.task_store.update(
            task_id,
            status="cancelled",
            error="Task cancelled by user.",
        )

        if task.process_group_id is not None:
            self._terminate_process_group_by_id(
                task.process_group_id
            )

        self.process_registry.remove(task_id)

        updated = self.task_store.get(task_id)

        return updated.to_dict() if updated else {
            "task_id": task_id,
            "status": "cancelled",
        }

    def _terminate_process_group_by_id(
        self,
        process_group_id: int,
    ) -> None:
        import time

        try:
            os.killpg(process_group_id, signal.SIGTERM)
        except ProcessLookupError:
            return

        deadline = (
            time.monotonic()
            + self.TERMINATION_GRACE_SECONDS
        )

        while time.monotonic() < deadline:
            try:
                os.killpg(process_group_id, 0)
            except ProcessLookupError:
                return

            time.sleep(0.1)

        try:
            os.killpg(process_group_id, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def cleanup_registered_processes(self) -> None:
        """إنهاء عمليات CrewAI المسجلة المتبقية من جلسة سابقة."""

        for task_id, info in self.process_registry.all().items():
            pid = info.get("pid")
            pgid = info.get("pgid")

            if not isinstance(pid, int) or not isinstance(pgid, int):
                self.process_registry.remove(task_id)
                continue

            cmdline_path = f"/proc/{pid}/cmdline"

            try:
                with open(cmdline_path, "rb") as file:
                    cmdline = file.read().replace(b"\x00", b" ").decode(
                        "utf-8",
                        errors="ignore",
                    )
            except OSError:
                self.process_registry.remove(task_id)
                continue

            # لا نقتل العملية إلا إذا كانت CrewAI فعلاً.
            if "crewai" not in cmdline.lower():
                self.process_registry.remove(task_id)
                continue

            try:
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass

            self.process_registry.remove(task_id)

    def _terminate_process_group(
        self,
        process: subprocess.Popen[str],
        process_group_id: int,
    ) -> None:
        try:
            os.killpg(process_group_id, signal.SIGTERM)

            try:
                process.wait(timeout=self.TERMINATION_GRACE_SECONDS)
                return
            except subprocess.TimeoutExpired:
                pass

            os.killpg(process_group_id, signal.SIGKILL)
            process.wait()

        except ProcessLookupError:
            return
