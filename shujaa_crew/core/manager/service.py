from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import replace
from threading import Event, Thread
from uuid import uuid4

from core.agents.contracts import AgentRegistryProtocol
from core.agents.executor_registry_contract import (
    AgentExecutorRegistryProtocol,
)
from core.runtime.process_registry import ProcessRegistry
from core.runtime.runner_contract import RunnerProtocol
from core.tasks.contracts import TaskStoreProtocol
from core.tasks.store import InMemoryTaskStore, TaskRecord
from core.work.models import (
    Execution,
    ExecutionStatus,
    Work,
    new_execution_id,
    new_work_id,
)
from core.work.registry import InMemoryWorkRegistry
from core.work.registry_contract import WorkRegistryProtocol
from core.work.execution_registry import InMemoryExecutionRegistry
from core.work.execution_registry_contract import (
    ExecutionRegistryProtocol,
)
from core.work.dispatcher import (
    DefaultExecutionDispatcher,
    DispatchRequest,
    ExecutionDispatcherProtocol,
)


class ShujaaManager:
    """المدير المركزي لاستقبال المهام ومتابعة حالتها."""

    MAX_COMMAND_LENGTH = 4000
    TASK_TIMEOUT_SECONDS = 120
    TERMINATION_GRACE_SECONDS = 5

    def __init__(
        self,
        crew_runner: RunnerProtocol,
        task_store: TaskStoreProtocol | None = None,
        process_registry: ProcessRegistry | None = None,
        work_registry: WorkRegistryProtocol | None = None,
        execution_registry: ExecutionRegistryProtocol | None = None,
        execution_dispatcher: ExecutionDispatcherProtocol | None = None,
        agent_registry: AgentRegistryProtocol | None = None,
        agent_executor_registry: AgentExecutorRegistryProtocol | None = None,
    ) -> None:
        self.crew_runner = crew_runner
        self.task_store = task_store or InMemoryTaskStore()
        self.process_registry = process_registry or ProcessRegistry()
        self.work_registry = (
            work_registry or InMemoryWorkRegistry()
        )
        self.execution_registry = (
            execution_registry or InMemoryExecutionRegistry()
        )
        self.execution_dispatcher = (
            execution_dispatcher
            or DefaultExecutionDispatcher(
                agent_registry=agent_registry,
                agent_executor_registry=agent_executor_registry,
            )
        )
        self.agent_registry = agent_registry
        self.agent_executor_registry = agent_executor_registry

    def submit(
        self,
        command: object,
        *,
        requested_agent_id: str | None = None,
        required_capability: str | None = None,
    ) -> dict[str, object]:
        if not isinstance(command, str):
            raise ValueError("Command must be a string.")

        command = command.strip()

        if not command:
            raise ValueError("Command is required.")

        if len(command) > self.MAX_COMMAND_LENGTH:
            raise ValueError("Command exceeds the allowed length.")

        work_id = new_work_id()
        task_id = str(uuid4())
        execution_id = new_execution_id()

        self.work_registry.create(
            Work(
                work_id=work_id,
                request=command,
            )
        )

        self.task_store.create(
            TaskRecord(
                task_id=task_id,
                work_id=work_id,
                command=command,
                status="queued",
            )
        )

        execution = Execution(
            execution_id=execution_id,
            work_id=work_id,
            task_id=task_id,
        )

        self.execution_registry.create(execution)

        dispatch_decision = self.execution_dispatcher.dispatch(
            DispatchRequest(
                work_id=work_id,
                task_id=task_id,
                execution_id=execution_id,
                command=command,
                requested_agent_id=requested_agent_id,
                required_capability=required_capability,
            )
        )

        execution = replace(
            execution,
            executor_id=dispatch_decision.executor_id,
        )
        self.execution_registry.save(execution)

        started = Event()

        Thread(
            target=self._execute_task,
            args=(
                task_id,
                execution_id,
                command,
                started,
                dispatch_decision.runtime_id,
                dispatch_decision.agent_id,
            ),
            daemon=True,
        ).start()

        started.wait(timeout=0.1)

        task = self.task_store.get(task_id)

        return {
            "status": "accepted",
            "work_id": work_id,
            "task_id": task_id,
            "execution_id": execution_id,
            "process_id": task.process_id if task else None,
            "message": "Shujaa accepted the task.",
        }

    def get_task(self, task_id: str) -> dict[str, object] | None:
        task = self.task_store.get(task_id)
        return task.to_dict() if task else None

    def _execute_task(
        self,
        task_id: str,
        execution_id: str,
        command: str,
        started: Event,
        runtime_id: str | None,
        agent_id: str | None,
    ) -> None:
        try:
            if runtime_id == "agent-executor":
                self._execute_agent_task(
                    task_id=task_id,
                    execution_id=execution_id,
                    command=command,
                    started=started,
                    agent_id=agent_id,
                )
                return

            if runtime_id not in {None, "process-runner"}:
                raise ValueError(
                    f"Unsupported execution runtime: {runtime_id}"
                )

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

            execution = self.execution_registry.get(execution_id)

            if execution is not None:
                self.execution_registry.save(
                    replace(
                        execution,
                        status=ExecutionStatus.RUNNING,
                    )
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

                execution = self.execution_registry.get(execution_id)

                if execution is not None:
                    self.execution_registry.save(
                        replace(
                            execution,
                            status=ExecutionStatus.TIMED_OUT,
                        )
                    )

                self.process_registry.remove(task_id)
                return

            current_task = self.task_store.get(task_id)

            if current_task and current_task.status == "cancelled":
                execution = self.execution_registry.get(execution_id)

                if execution is not None:
                    self.execution_registry.save(
                        replace(
                            execution,
                            status=ExecutionStatus.CANCELLED,
                        )
                    )

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

                execution = self.execution_registry.get(execution_id)

                if execution is not None:
                    self.execution_registry.save(
                        replace(
                            execution,
                            status=ExecutionStatus.COMPLETED,
                        )
                    )
            else:
                error_reader = getattr(
                    self.crew_runner,
                    "get_error",
                    None,
                )

                if callable(error_reader):
                    error_message = error_reader(return_code)
                else:
                    error_message = f"Exit code: {return_code}"

                self.task_store.update(
                    task_id,
                    status="failed",
                    error=error_message,
                )

                execution = self.execution_registry.get(execution_id)

                if execution is not None:
                    self.execution_registry.save(
                        replace(
                            execution,
                            status=ExecutionStatus.FAILED,
                        )
                    )

            self.process_registry.remove(task_id)

        except Exception as error:
            self.task_store.update(
                task_id,
                status="failed",
                error=str(error),
            )

            execution = self.execution_registry.get(execution_id)

            if execution is not None:
                self.execution_registry.save(
                    replace(
                        execution,
                        status=ExecutionStatus.FAILED,
                    )
                )

            started.set()

    def _execute_agent_task(
        self,
        *,
        task_id: str,
        execution_id: str,
        command: str,
        started: Event,
        agent_id: str | None,
    ) -> None:
        if agent_id is None:
            raise ValueError(
                "Agent execution requires agent_id."
            )

        if self.agent_registry is None:
            raise ValueError(
                "Agent registry is not configured."
            )

        if self.agent_executor_registry is None:
            raise ValueError(
                "Agent executor registry is not configured."
            )

        agent = self.agent_registry.get(agent_id)

        if agent is None:
            raise ValueError(
                f"Agent not found: {agent_id}"
            )

        if not agent.enabled:
            raise ValueError(
                f"Agent is disabled: {agent_id}"
            )

        executor = self.agent_executor_registry.get(agent_id)

        if executor is None:
            raise ValueError(
                f"No executor registered for agent: {agent_id}"
            )

        self.task_store.update(
            task_id,
            status="running",
        )

        execution = self.execution_registry.get(execution_id)

        if execution is not None:
            self.execution_registry.save(
                replace(
                    execution,
                    status=ExecutionStatus.RUNNING,
                )
            )

        started.set()

        result = executor.execute(
            agent,
            command,
        )

        current_task = self.task_store.get(task_id)

        if current_task and current_task.status == "cancelled":
            execution = self.execution_registry.get(execution_id)

            if execution is not None:
                self.execution_registry.save(
                    replace(
                        execution,
                        status=ExecutionStatus.CANCELLED,
                    )
                )

            return

        self.task_store.update(
            task_id,
            status="completed",
            result=result,
        )

        execution = self.execution_registry.get(execution_id)

        if execution is not None:
            self.execution_registry.save(
                replace(
                    execution,
                    status=ExecutionStatus.COMPLETED,
                )
            )

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
