from __future__ import annotations

import os
import signal
import subprocess
from threading import Event, Thread
from uuid import uuid4

from core.agents.contracts import AgentRegistryProtocol
from core.agents.executor_registry_contract import (
    AgentExecutorRegistryProtocol,
)
from core.runtime.process_registry import ProcessRegistry
from core.runtime.process_registry_contract import (
    CleanupDisposition,
    CleanupResult,
    ProcessOwnership,
    ProcessRegistryProtocol,
    RegistrationDisposition,
    ReleaseDisposition,
)
from core.runtime.runner_contract import RunnerProtocol
from core.tasks.contracts import TaskStoreProtocol
from core.tasks.store import InMemoryTaskStore, TaskRecord
from core.work.models import (
    Execution,
    ExecutionStatus,
    RetrySafety,
    Work,
    new_execution_id,
    new_work_id,
)
from core.work.registry import InMemoryWorkRegistry
from core.work.registry_contract import WorkRegistryProtocol
from core.work.execution_registry import InMemoryExecutionRegistry
from core.work.execution_registry_contract import (
    ExecutionRegistryProtocol,
    RetryAdmissionResult,
    TransitionDisposition,
    TransitionResult,
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
        process_registry: ProcessRegistryProtocol | None = None,
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

    _TERMINAL_EXECUTION_STATUSES = frozenset(
        {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMED_OUT,
        }
    )

    _RETRYABLE_EXECUTION_STATUSES = frozenset(
        {
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMED_OUT,
        }
    )

    _ALLOWED_EXECUTION_TRANSITIONS = {
        ExecutionStatus.QUEUED: frozenset(
            {
                ExecutionStatus.RUNNING,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
            }
        ),
        ExecutionStatus.RUNNING: (
            _TERMINAL_EXECUTION_STATUSES
        ),
    }

    def _transition_execution(
        self,
        execution_id: str,
        *,
        target_status: ExecutionStatus,
        operation_id: str,
        error: str | None = None,
        result: str | None = None,
    ):
        """Authorize semantics, then request an atomic commit."""
        execution = self.execution_registry.get(execution_id)

        if execution is None:
            raise ValueError(
                f"Execution does not exist: {execution_id}"
            )

        allowed_targets = (
            self._ALLOWED_EXECUTION_TRANSITIONS.get(
                execution.status,
                frozenset(),
            )
        )

        is_terminal_observation = (
            execution.status
            in self._TERMINAL_EXECUTION_STATUSES
            and target_status
            in self._TERMINAL_EXECUTION_STATUSES
        )

        if (
            target_status not in allowed_targets
            and not is_terminal_observation
        ):
            raise ValueError(
                "Invalid execution transition: "
                f"{execution.status.value} -> "
                f"{target_status.value}"
            )

        return self.execution_registry.transition(
            execution_id,
            target_status=target_status,
            expected_version=execution.state_version,
            operation_id=operation_id,
            error=error,
            result=result,
            source="manager_lifecycle_authority",
        )

    def _reconcile_terminal_execution(
        self,
        task_id: str,
        execution_id: str,
        *,
        target_status: ExecutionStatus,
        operation_id: str,
        error: str | None = None,
        result: str | None = None,
    ) -> TransitionResult:
        """Commit an observation, then mirror the registry winner."""
        transition = self._transition_execution(
            execution_id,
            target_status=target_status,
            operation_id=operation_id,
            error=error,
            result=result,
        )

        if (
            transition.disposition
            == TransitionDisposition.STALE_VERSION
            and transition.execution.status
            not in self._TERMINAL_EXECUTION_STATUSES
        ):
            transition = self._transition_execution(
                execution_id,
                target_status=target_status,
                operation_id=operation_id,
                error=error,
                result=result,
            )

        known_dispositions = {
            TransitionDisposition.APPLIED,
            TransitionDisposition.STALE_VERSION,
            TransitionDisposition.IDEMPOTENT_REPLAY,
            (
                TransitionDisposition
                .CONFLICTING_TERMINAL_ATTEMPT
            ),
        }

        if transition.disposition not in known_dispositions:
            raise RuntimeError(
                "Unknown execution transition disposition: "
                f"{transition.disposition}"
            )

        self.task_store.update(
            task_id,
            status=transition.execution.status.value,
            error=transition.execution.error,
            result=transition.execution.result,
        )

        return transition

    def _authorize_retry_source(
        self,
        source_execution_id: str,
        *,
        operation_id: str,
    ) -> Execution:
        source = self.execution_registry.get(
            source_execution_id
        )

        if source is None:
            raise ValueError(
                "Source execution does not exist: "
                f"{source_execution_id}"
            )

        if source.retry_safety != RetrySafety.DECLARED_SAFE:
            raise ValueError(
                "Execution is not declared safe to retry."
            )

        if (
            source.status
            not in self._RETRYABLE_EXECUTION_STATUSES
        ):
            raise ValueError(
                "Execution status is not retryable: "
                f"{source.status.value}"
            )

        if (
            not isinstance(operation_id, str)
            or not operation_id.strip()
        ):
            raise ValueError(
                "Retry operation ID is required."
            )

        return source

    def admit_retry(
        self,
        source_execution_id: str,
        *,
        operation_id: str,
    ) -> RetryAdmissionResult:
        """Authorize and atomically admit a retry attempt."""
        self._authorize_retry_source(
            source_execution_id,
            operation_id=operation_id,
        )

        return self.execution_registry.admit_retry(
            source_execution_id,
            execution_id=new_execution_id(),
            operation_id=operation_id,
        )

    def retry_task(
        self,
        source_execution_id: str,
        *,
        operation_id: str,
    ) -> RetryAdmissionResult:
        """Dispatch then atomically admit a retry attempt."""
        source = self._authorize_retry_source(
            source_execution_id,
            operation_id=operation_id,
        )

        existing_retry = next(
            (
                execution
                for execution
                in self.execution_registry.list_by_task(
                    source.task_id
                )
                if (
                    execution.previous_execution_id
                    == source_execution_id
                )
            ),
            None,
        )

        if existing_retry is not None:
            return self.execution_registry.admit_retry(
                source_execution_id,
                execution_id=new_execution_id(),
                operation_id=operation_id,
            )

        task = self.task_store.get(source.task_id)

        if task is None:
            raise ValueError(
                f"Task not found: {source.task_id}"
            )

        retry_execution_id = new_execution_id()

        dispatch_decision = (
            self.execution_dispatcher.dispatch(
                DispatchRequest(
                    work_id=source.work_id,
                    task_id=source.task_id,
                    execution_id=retry_execution_id,
                    command=task.command,
                    requested_agent_id=(
                        source.requested_agent_id
                    ),
                    required_capability=(
                        source.required_capability
                    ),
                )
            )
        )

        admission = self.execution_registry.admit_retry(
            source_execution_id,
            execution_id=retry_execution_id,
            operation_id=operation_id,
            executor_id=dispatch_decision.executor_id,
        )

        if not admission.applied:
            return admission

        self.task_store.update(
            source.task_id,
            status="queued",
            error=None,
            result=None,
        )

        started = Event()

        Thread(
            target=self._execute_task,
            args=(
                source.task_id,
                admission.execution.execution_id,
                task.command,
                started,
                dispatch_decision.runtime_id,
                dispatch_decision.agent_id,
            ),
            daemon=True,
        ).start()

        started.wait(timeout=0.1)

        return admission

    def submit(
        self,
        command: object,
        *,
        requested_agent_id: str | None = None,
        required_capability: str | None = None,
        retry_safety: RetrySafety = RetrySafety.DENY,
    ) -> dict[str, object]:
        if not isinstance(command, str):
            raise ValueError("Command must be a string.")

        command = command.strip()

        if not command:
            raise ValueError("Command is required.")

        if len(command) > self.MAX_COMMAND_LENGTH:
            raise ValueError("Command exceeds the allowed length.")

        if not isinstance(retry_safety, RetrySafety):
            raise ValueError(
                "Retry safety must be a RetrySafety value."
            )

        work_id = new_work_id()
        task_id = str(uuid4())
        execution_id = new_execution_id()

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
            executor_id=dispatch_decision.executor_id,
            retry_safety=retry_safety,
            requested_agent_id=requested_agent_id,
            required_capability=required_capability,
        )

        self.execution_registry.create(execution)

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

    @staticmethod
    def _read_process_start_time_ticks(
        pid: int,
    ) -> int | None:
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
                f"Unable to read process identity for PID {pid}."
            ) from error

        closing_parenthesis = stat.rfind(")")

        if closing_parenthesis < 0:
            raise RuntimeError(
                f"Malformed process identity for PID {pid}."
            )

        remaining_fields = stat[
            closing_parenthesis + 1:
        ].split()

        if len(remaining_fields) <= 19:
            raise RuntimeError(
                f"Malformed process identity for PID {pid}."
            )

        try:
            start_time = int(remaining_fields[19])
        except ValueError as error:
            raise RuntimeError(
                f"Malformed process identity for PID {pid}."
            ) from error

        if start_time <= 0:
            raise RuntimeError(
                f"Invalid process identity for PID {pid}."
            )

        return start_time

    def _execute_task(
        self,
        task_id: str,
        execution_id: str,
        command: str,
        started: Event,
        runtime_id: str | None,
        agent_id: str | None,
    ) -> None:
        process = None
        process_group_id = None
        process_has_exited = False
        process_owner_registered = False
        process_termination_attempted = False
        process_termination_succeeded = False

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

            ownership = ProcessOwnership(
                task_id=task_id,
                execution_id=execution_id,
                pid=process.pid,
                pgid=process_group_id,
                process_start_time_ticks=(
                    self._read_process_start_time_ticks(
                        process.pid
                    )
                ),
            )
            registration = self.process_registry.register(
                ownership
            )

            if (
                registration.disposition
                == RegistrationDisposition.OWNER_CONFLICT
            ):
                process_termination_attempted = True
                self._terminate_process_group(
                    process,
                    process_group_id,
                )
                process_termination_succeeded = True
                raise RuntimeError(
                    "Process ownership conflict for task: "
                    f"{task_id}"
                )

            process_owner_registered = True

            self.task_store.update(
                task_id,
                status="running",
                process_id=process.pid,
                process_group_id=process_group_id,
            )

            self._transition_execution(
                execution_id,
                target_status=ExecutionStatus.RUNNING,
                operation_id=f"{execution_id}:running",
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
                transition = self._reconcile_terminal_execution(
                    task_id,
                    execution_id,
                    target_status=ExecutionStatus.TIMED_OUT,
                    operation_id=f"{execution_id}:timed_out",
                    error=(
                        f"Task exceeded "
                        f"{self.TASK_TIMEOUT_SECONDS} seconds."
                    ),
                )

                if (
                    transition.disposition
                    == TransitionDisposition.APPLIED
                ):
                    self._terminate_process_group(
                        process,
                        process_group_id,
                    )
                    self.process_registry.release(
                        task_id,
                        expected_execution_id=execution_id,
                    )

                return

            process_has_exited = True

            if return_code == 0:
                result = None
                result_reader = getattr(
                    self.crew_runner,
                    "get_result",
                    None,
                )

                if callable(result_reader):
                    result = result_reader(process)

                self._reconcile_terminal_execution(
                    task_id,
                    execution_id,
                    target_status=ExecutionStatus.COMPLETED,
                    operation_id=f"{execution_id}:completed",
                    error=None,
                    result=result,
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

                self._reconcile_terminal_execution(
                    task_id,
                    execution_id,
                    target_status=ExecutionStatus.FAILED,
                    operation_id=f"{execution_id}:failed",
                    error=error_message,
                )

            self.process_registry.release(
                task_id,
                expected_execution_id=execution_id,
            )

        except Exception as error:
            if (
                process is not None
                and process_group_id is not None
                and not process_has_exited
                and not process_termination_attempted
            ):
                process_termination_attempted = True

                try:
                    self._terminate_process_group(
                        process,
                        process_group_id,
                    )
                except Exception:
                    process_termination_succeeded = False
                else:
                    process_termination_succeeded = True

            self._reconcile_terminal_execution(
                task_id,
                execution_id,
                target_status=ExecutionStatus.FAILED,
                operation_id=f"{execution_id}:failed",
                error=str(error),
            )

            if (
                process_owner_registered
                and (
                    process_has_exited
                    or process_termination_succeeded
                )
            ):
                self.process_registry.release(
                    task_id,
                    expected_execution_id=execution_id,
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

        self._transition_execution(
            execution_id,
            target_status=ExecutionStatus.RUNNING,
            operation_id=f"{execution_id}:running",
        )

        started.set()

        result = executor.execute(
            agent,
            command,
        )

        self._reconcile_terminal_execution(
            task_id,
            execution_id,
            target_status=ExecutionStatus.COMPLETED,
            operation_id=f"{execution_id}:completed",
            result=result,
        )

    def _cleanup_process_ownership(
        self,
        task_id: str,
        *,
        expected_execution_id: str,
    ) -> CleanupResult:
        ownership = self.process_registry.get(task_id)

        if ownership is None:
            return CleanupResult(
                disposition=CleanupDisposition.NOT_OWNED,
                ownership=None,
            )

        if ownership.execution_id != expected_execution_id:
            return CleanupResult(
                disposition=CleanupDisposition.OWNER_MISMATCH,
                ownership=ownership,
            )

        try:
            current_start_time = (
                self._read_process_start_time_ticks(
                    ownership.pid
                )
            )
        except Exception as error:
            return CleanupResult(
                disposition=(
                    CleanupDisposition
                    .IDENTITY_CHECK_FAILED_RETAINED
                ),
                ownership=ownership,
                error=str(error),
            )

        if current_start_time is None:
            release = self.process_registry.release(
                task_id,
                expected_execution_id=expected_execution_id,
            )

            if (
                release.disposition
                == ReleaseDisposition.RELEASED
            ):
                return CleanupResult(
                    disposition=(
                        CleanupDisposition
                        .ALREADY_EXITED_AND_RELEASED
                    ),
                    ownership=release.ownership,
                )

            if (
                release.disposition
                == ReleaseDisposition.OWNER_MISMATCH
            ):
                return CleanupResult(
                    disposition=(
                        CleanupDisposition.OWNER_MISMATCH
                    ),
                    ownership=release.ownership,
                )

            return CleanupResult(
                disposition=CleanupDisposition.NOT_OWNED,
                ownership=None,
            )

        if (
            ownership.process_start_time_ticks is None
            or current_start_time
            != ownership.process_start_time_ticks
        ):
            return CleanupResult(
                disposition=CleanupDisposition.IDENTITY_MISMATCH,
                ownership=ownership,
            )

        try:
            current_process_group_id = os.getpgid(
                ownership.pid
            )
        except OSError as error:
            return CleanupResult(
                disposition=(
                    CleanupDisposition
                    .IDENTITY_CHECK_FAILED_RETAINED
                ),
                ownership=ownership,
                error=str(error),
            )

        if current_process_group_id != ownership.pgid:
            return CleanupResult(
                disposition=(
                    CleanupDisposition.PROCESS_GROUP_MISMATCH
                ),
                ownership=ownership,
            )

        try:
            self._terminate_process_group_by_id(
                ownership.pgid
            )
        except Exception as error:
            return CleanupResult(
                disposition=(
                    CleanupDisposition
                    .TERMINATION_FAILED_RETAINED
                ),
                ownership=ownership,
                error=str(error),
            )

        release = self.process_registry.release(
            task_id,
            expected_execution_id=expected_execution_id,
        )

        if release.disposition == ReleaseDisposition.RELEASED:
            return CleanupResult(
                disposition=(
                    CleanupDisposition.TERMINATED_AND_RELEASED
                ),
                ownership=release.ownership,
            )

        if (
            release.disposition
            == ReleaseDisposition.OWNER_MISMATCH
        ):
            return CleanupResult(
                disposition=CleanupDisposition.OWNER_MISMATCH,
                ownership=release.ownership,
            )

        return CleanupResult(
            disposition=CleanupDisposition.NOT_OWNED,
            ownership=None,
        )

    def cancel_task(self, task_id: str) -> dict[str, object]:
        task = self.task_store.get(task_id)

        if task is None:
            raise ValueError("Task not found.")

        executions = self.execution_registry.list_by_task(task_id)

        if not executions:
            raise ValueError("Execution not found.")

        execution = max(
            executions,
            key=lambda candidate: candidate.created_at,
        )
        transition = self._reconcile_terminal_execution(
            task_id,
            execution.execution_id,
            target_status=ExecutionStatus.CANCELLED,
            operation_id=(
                f"{execution.execution_id}:cancelled"
            ),
            error="Task cancelled by user.",
        )

        cleanup_result = None

        if (
            transition.execution.status
            == ExecutionStatus.CANCELLED
            and transition.disposition
            in {
                TransitionDisposition.APPLIED,
                TransitionDisposition.IDEMPOTENT_REPLAY,
            }
        ):
            cleanup_result = self._cleanup_process_ownership(
                task_id,
                expected_execution_id=(
                    execution.execution_id
                ),
            )

        updated = self.task_store.get(task_id)

        response = (
            updated.to_dict()
            if updated
            else {
                "task_id": task_id,
                "status": transition.execution.status.value,
            }
        )
        response["cleanup_disposition"] = (
            cleanup_result.disposition.value
            if cleanup_result
            else None
        )
        response["cleanup_error"] = (
            cleanup_result.error
            if cleanup_result
            else None
        )

        return response

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
            return

        confirmation_deadline = (
            time.monotonic()
            + self.TERMINATION_GRACE_SECONDS
        )

        while True:
            try:
                os.killpg(process_group_id, 0)
            except ProcessLookupError:
                return

            if time.monotonic() >= confirmation_deadline:
                break

            time.sleep(0.1)

        raise RuntimeError(
            "Process group survived SIGKILL: "
            f"{process_group_id}"
        )

    def cleanup_registered_processes(
        self,
    ) -> dict[str, CleanupResult]:
        """Clean ownership retained from an earlier session."""

        ownerships = self.process_registry.all()
        results: dict[str, CleanupResult] = {}

        for task_id, ownership in ownerships.items():
            results[task_id] = (
                self._cleanup_process_ownership(
                    task_id,
                    expected_execution_id=(
                        ownership.execution_id
                    ),
                )
            )

        return results

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
