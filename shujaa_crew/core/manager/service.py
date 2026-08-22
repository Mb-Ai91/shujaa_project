from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
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
from core.work.event_store import (
    AppendReceipt,
    AuditStoreProtocol,
    EventStoreProtocol,
    InMemoryAuditStore,
    InMemoryEventStore,
)
from core.work.events import AuditRecord, WorkEvent
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



@dataclass(frozen=True)
class CleanupEventOutcome:
    """Manager result separating cleanup from event persistence."""

    cleanup_result: CleanupResult
    event_append_receipt: AppendReceipt

    @property
    def disposition(self) -> CleanupDisposition:
        return self.cleanup_result.disposition

    @property
    def ownership(self) -> ProcessOwnership | None:
        return self.cleanup_result.ownership

    @property
    def error(self) -> str | None:
        return self.cleanup_result.error


@dataclass(frozen=True)
class RetryEventOutcome:
    """Manager result separating admission from event persistence."""

    admission_result: RetryAdmissionResult
    admission_event_append_receipt: AppendReceipt
    audit_append_receipt: AppendReceipt

    @property
    def applied(self) -> bool:
        return self.admission_result.applied

    @property
    def disposition(self):
        return self.admission_result.disposition

    @property
    def execution(self) -> Execution:
        return self.admission_result.execution

    @property
    def event_append_receipt(self) -> AppendReceipt | None:
        return self.admission_result.event_append_receipt


class RetryAdmissionDeniedError(ValueError):
    """Structured retry denial with an isolated event receipt."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: str,
        admission_event_append_receipt: (
            AppendReceipt | None
        ),
        audit_append_receipt: AppendReceipt | None,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.admission_event_append_receipt = (
            admission_event_append_receipt
        )
        self.audit_append_receipt = audit_append_receipt


class AuditedCancelError(ValueError):
    """Cancel rejection retaining its separate Audit receipt."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: str,
        audit_append_receipt: AppendReceipt | None,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.audit_append_receipt = audit_append_receipt


class AuditedDispatchRejectionError(ValueError):
    """Dispatch rejection retaining its separate Audit receipt."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: str,
        audit_append_receipt: AppendReceipt,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.audit_append_receipt = audit_append_receipt


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
        event_store: EventStoreProtocol | None = None,
        audit_store: AuditStoreProtocol | None = None,
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
        self.event_store = (
            event_store or InMemoryEventStore()
        )
        self.audit_store = (
            audit_store or InMemoryAuditStore()
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

    @staticmethod
    def _submit_audit_operation_id(
        work_id: str,
    ) -> str:
        return f"{work_id}:submit"

    @classmethod
    def _submit_audit_id(
        cls,
        work_id: str,
    ) -> str:
        operation_id = (
            cls._submit_audit_operation_id(work_id)
        )
        material = json.dumps(
            [operation_id, work_id],
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        digest = sha256(material).hexdigest()
        return f"audit-work-submit-{digest}"

    def _append_submit_audit(
        self,
        *,
        work_id: str,
        outcome: str,
        reason_code: str,
        event_id: str | None = None,
        error_code: str | None = None,
        actor_type: str = "system",
        actor_id: str = "shujaa_manager",
    ) -> AppendReceipt:
        audit = AuditRecord(
            audit_id=self._submit_audit_id(work_id),
            action="work.submit",
            actor_type=actor_type,
            actor_id=actor_id,
            resource_type="work",
            resource_id=work_id,
            outcome=outcome,
            reason_code=reason_code,
            operation_id=(
                self._submit_audit_operation_id(
                    work_id
                )
            ),
            event_id=event_id,
            error_code=error_code,
        )

        return self.audit_store.append(audit)

    @staticmethod
    def _operation_audit_id(
        prefix: str,
        operation_id: str,
        resource_id: str,
    ) -> str:
        material = json.dumps(
            [operation_id, resource_id],
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        digest = sha256(material).hexdigest()
        return f"{prefix}{digest}"

    @classmethod
    def _retry_audit_id(
        cls,
        operation_id: str,
        source_execution_id: str,
    ) -> str:
        return cls._operation_audit_id(
            "audit-execution-retry-",
            operation_id,
            source_execution_id,
        )

    @classmethod
    def _cancel_audit_id(
        cls,
        cancel_operation_id: str,
        task_id: str,
    ) -> str:
        return cls._operation_audit_id(
            "audit-task-cancel-",
            cancel_operation_id,
            task_id,
        )

    def _append_retry_audit(
        self,
        *,
        source_execution_id: str,
        operation_id: str,
        outcome: str,
        reason_code: str,
        event_id: str | None,
    ) -> AppendReceipt:
        audit = AuditRecord(
            audit_id=self._retry_audit_id(
                operation_id,
                source_execution_id,
            ),
            action="execution.retry",
            actor_type="system",
            actor_id="shujaa_manager",
            resource_type="execution",
            resource_id=source_execution_id,
            outcome=outcome,
            reason_code=reason_code,
            operation_id=operation_id,
            event_id=event_id,
        )
        return self.audit_store.append_replay_stable(
            audit
        )

    def _append_retry_result_audit(
        self,
        admission: RetryAdmissionResult,
        *,
        source_execution_id: str,
        operation_id: str,
        event_id: str,
    ) -> AppendReceipt:
        disposition = admission.disposition.value
        if disposition in {
            "applied",
            "idempotent_replay",
        }:
            outcome = "accepted"
            reason_code = "retry_admitted"
        else:
            outcome = "rejected"
            reason_code = disposition

        return self._append_retry_audit(
            source_execution_id=source_execution_id,
            operation_id=operation_id,
            outcome=outcome,
            reason_code=reason_code,
            event_id=event_id,
        )

    def _append_cancel_audit(
        self,
        *,
        task_id: str,
        cancel_operation_id: str,
        outcome: str,
        reason_code: str,
        event_id: str | None,
    ) -> AppendReceipt:
        audit = AuditRecord(
            audit_id=self._cancel_audit_id(
                cancel_operation_id,
                task_id,
            ),
            action="task.cancel",
            actor_type="system",
            actor_id="shujaa_manager",
            resource_type="task",
            resource_id=task_id,
            outcome=outcome,
            reason_code=reason_code,
            operation_id=cancel_operation_id,
            event_id=event_id,
        )
        return self.audit_store.append_replay_stable(
            audit
        )

    def _cancel_rejection_error(
        self,
        message: str,
        *,
        task_id: str,
        cancel_operation_id: str,
        reason_code: str,
    ) -> AuditedCancelError:
        receipt = self._append_cancel_audit(
            task_id=task_id,
            cancel_operation_id=cancel_operation_id,
            outcome="rejected",
            reason_code=reason_code,
            event_id=None,
        )
        return AuditedCancelError(
            message,
            reason_code=reason_code,
            audit_append_receipt=receipt,
        )

    @staticmethod
    def _transition_event_id(
        operation_id: str,
    ) -> str:
        return (
            "event-execution-transition-"
            f"{operation_id}"
        )

    def _append_transition_event(
        self,
        transition: TransitionResult,
        *,
        target_status: ExecutionStatus,
        operation_id: str,
    ):
        event_id = self._transition_event_id(
            operation_id
        )

        if (
            transition.disposition
            == TransitionDisposition.IDEMPOTENT_REPLAY
        ):
            existing = self.event_store.get(event_id)

            if existing is not None:
                return self.event_store.append(
                    existing.record
                )

        execution = transition.execution

        payload: dict[str, str | int] = {
            "disposition": transition.disposition.value,
            "status": execution.status.value,
            "state_version": execution.state_version,
        }

        if transition.observation is not None:
            payload.update(
                {
                    "attempted_status": (
                        transition.observation
                        .attempted_status.value
                    ),
                    "winner_status": (
                        execution.status.value
                    ),
                    "rejected_at_version": (
                        transition.observation
                        .rejected_at_version
                    ),
                }
            )
        elif not transition.applied:
            payload["attempted_status"] = (
                target_status.value
            )

        event = WorkEvent(
            event_id=event_id,
            event_type=(
                "execution.transition."
                f"{transition.disposition.value}"
            ),
            entity_type="execution",
            entity_id=execution.execution_id,
            source_component="core.manager.lifecycle",
            correlation_id=execution.work_id,
            operation_id=operation_id,
            work_id=execution.work_id,
            task_id=execution.task_id,
            execution_id=execution.execution_id,
            payload=payload,
        )

        return self.event_store.append(event)

    @staticmethod
    def _cleanup_event_id(
        cleanup_operation_id: str,
        task_id: str,
    ) -> str:
        payload = json.dumps(
            [cleanup_operation_id, task_id],
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        digest = sha256(payload).hexdigest()
        return f"event-process-cleanup-{digest}"

    def _append_cleanup_event(
        self,
        cleanup_result: CleanupResult,
        *,
        task_id: str,
        cleanup_operation_id: str,
        trigger: str,
        work_id: str | None,
    ) -> AppendReceipt:
        ownership_retained = (
            cleanup_result.disposition
            in {
                CleanupDisposition.OWNER_MISMATCH,
                CleanupDisposition.IDENTITY_MISMATCH,
                CleanupDisposition.PROCESS_GROUP_MISMATCH,
                (
                    CleanupDisposition
                    .IDENTITY_CHECK_FAILED_RETAINED
                ),
                (
                    CleanupDisposition
                    .TERMINATION_FAILED_RETAINED
                ),
            }
        )

        event = WorkEvent(
            event_id=self._cleanup_event_id(
                cleanup_operation_id,
                task_id,
            ),
            event_type=(
                "process_ownership.cleanup."
                f"{cleanup_result.disposition.value}"
            ),
            entity_type="process_ownership",
            entity_id=task_id,
            source_component="core.manager.cleanup",
            correlation_id=work_id or task_id,
            operation_id=cleanup_operation_id,
            work_id=work_id,
            task_id=task_id,
            execution_id=(
                cleanup_result.ownership.execution_id
                if cleanup_result.ownership
                else None
            ),
            payload={
                "disposition": (
                    cleanup_result.disposition.value
                ),
                "ownership_retained": ownership_retained,
                "trigger": trigger,
            },
        )

        return self.event_store.append_replay_stable(event)

    @staticmethod
    def _dispatch_event_id(
        execution_id: str,
    ) -> str:
        return (
            "event-execution-dispatched-"
            f"{execution_id}"
        )

    def _append_dispatch_event(
        self,
        *,
        work_id: str,
        task_id: str,
        execution_id: str,
        executor_id: str,
        runtime_id: str | None,
        agent_id: str | None,
        requested_agent_id: str | None,
        required_capability: str | None,
        operation_id: str,
    ) -> AppendReceipt:
        payload: dict[str, object] = {
            "executor_id": executor_id,
        }

        if runtime_id is not None:
            payload["runtime_id"] = runtime_id

        if agent_id is not None:
            payload["agent_id"] = agent_id

        if requested_agent_id is not None:
            payload["requested_agent_id"] = (
                requested_agent_id
            )

        event = WorkEvent(
            event_id=self._dispatch_event_id(
                execution_id
            ),
            event_type="execution.dispatched",
            entity_type="execution",
            entity_id=execution_id,
            source_component="core.manager",
            correlation_id=work_id,
            operation_id=operation_id,
            work_id=work_id,
            task_id=task_id,
            execution_id=execution_id,
            capability_asset_id=required_capability,
            payload=payload,
        )

        return self.event_store.append(event)

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

        transition = self.execution_registry.transition(
            execution_id,
            target_status=target_status,
            expected_version=execution.state_version,
            operation_id=operation_id,
            error=error,
            result=result,
            source="manager_lifecycle_authority",
        )

        event_append_receipt = (
            self._append_transition_event(
                transition,
                target_status=target_status,
                operation_id=operation_id,
            )
        )

        return replace(
            transition,
            event_append_receipt=event_append_receipt,
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

    @staticmethod
    def _retry_admission_event_id(
        operation_id: str,
        source_execution_id: str,
    ) -> str:
        material = json.dumps(
            [operation_id, source_execution_id],
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        digest = sha256(material).hexdigest()
        return (
            "event-execution-retry-admission-"
            f"{digest}"
        )

    def _append_retry_admission_event(
        self,
        admission: RetryAdmissionResult,
        *,
        source: Execution,
        operation_id: str,
    ) -> AppendReceipt:
        disposition = admission.disposition.value

        if disposition == "idempotent_replay":
            disposition = "applied"

        event = WorkEvent(
            event_id=self._retry_admission_event_id(
                operation_id,
                source.execution_id,
            ),
            event_type=(
                "execution.retry_admission."
                f"{disposition}"
            ),
            entity_type="execution",
            entity_id=source.execution_id,
            source_component=(
                "core.manager.retry_admission"
            ),
            correlation_id=source.work_id,
            operation_id=operation_id,
            work_id=source.work_id,
            task_id=source.task_id,
            execution_id=(
                admission.execution.execution_id
            ),
            payload={"disposition": disposition},
        )

        return self.event_store.append_replay_stable(
            event
        )

    def _append_retry_denial_event(
        self,
        *,
        source_execution_id: str,
        operation_id: str,
        reason_code: str,
        source: Execution | None,
    ) -> AppendReceipt:
        event = WorkEvent(
            event_id=self._retry_admission_event_id(
                operation_id,
                source_execution_id,
            ),
            event_type=(
                "execution.retry_admission.denied"
            ),
            entity_type="execution",
            entity_id=source_execution_id,
            source_component=(
                "core.manager.retry_admission"
            ),
            correlation_id=(
                source.work_id
                if source
                else source_execution_id
            ),
            operation_id=operation_id,
            work_id=(
                source.work_id if source else None
            ),
            task_id=(
                source.task_id if source else None
            ),
            execution_id=None,
            payload={
                "disposition": "denied",
                "reason_code": reason_code,
            },
        )

        return self.event_store.append_replay_stable(
            event
        )

    def _retry_denied_error(
        self,
        message: str,
        *,
        reason_code: str,
        source_execution_id: str,
        operation_id: str,
        source: Execution | None,
    ) -> RetryAdmissionDeniedError:
        event_receipt = self._append_retry_denial_event(
            source_execution_id=source_execution_id,
            operation_id=operation_id,
            reason_code=reason_code,
            source=source,
        )
        audit_receipt = self._append_retry_audit(
            source_execution_id=source_execution_id,
            operation_id=operation_id,
            outcome="rejected",
            reason_code=reason_code,
            event_id=event_receipt.record_id,
        )
        return RetryAdmissionDeniedError(
            message,
            reason_code=reason_code,
            admission_event_append_receipt=event_receipt,
            audit_append_receipt=audit_receipt,
        )

    def _authorize_retry_source(
        self,
        source_execution_id: str,
        *,
        operation_id: str,
    ) -> Execution:
        if (
            not isinstance(operation_id, str)
            or not operation_id.strip()
        ):
            raise RetryAdmissionDeniedError(
                "Retry operation ID is required.",
                reason_code="invalid_operation_id",
                admission_event_append_receipt=None,
                audit_append_receipt=None,
            )

        source = self.execution_registry.get(
            source_execution_id
        )

        if source is None:
            raise self._retry_denied_error(
                "Source execution does not exist: "
                f"{source_execution_id}",
                reason_code=(
                    "source_execution_not_found"
                ),
                source_execution_id=source_execution_id,
                operation_id=operation_id,
                source=None,
            )

        if source.retry_safety != RetrySafety.DECLARED_SAFE:
            raise self._retry_denied_error(
                "Execution is not declared safe to retry.",
                reason_code="retry_not_declared_safe",
                source_execution_id=source_execution_id,
                operation_id=operation_id,
                source=source,
            )

        if (
            source.status
            not in self._RETRYABLE_EXECUTION_STATUSES
        ):
            raise self._retry_denied_error(
                "Execution status is not retryable: "
                f"{source.status.value}",
                reason_code="status_not_retryable",
                source_execution_id=source_execution_id,
                operation_id=operation_id,
                source=source,
            )

        return source

    def admit_retry(
        self,
        source_execution_id: str,
        *,
        operation_id: str,
    ) -> RetryEventOutcome:
        """Authorize and atomically admit a retry attempt."""
        source = self._authorize_retry_source(
            source_execution_id,
            operation_id=operation_id,
        )

        admission = self.execution_registry.admit_retry(
            source_execution_id,
            execution_id=new_execution_id(),
            operation_id=operation_id,
        )
        event_receipt = self._append_retry_admission_event(
            admission,
            source=source,
            operation_id=operation_id,
        )
        audit_receipt = self._append_retry_result_audit(
            admission,
            source_execution_id=source.execution_id,
            operation_id=operation_id,
            event_id=event_receipt.record_id,
        )
        return RetryEventOutcome(
            admission_result=admission,
            admission_event_append_receipt=event_receipt,
            audit_append_receipt=audit_receipt,
        )

    def retry_task(
        self,
        source_execution_id: str,
        *,
        operation_id: str,
    ) -> RetryEventOutcome:
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
            admission = (
                self.execution_registry.admit_retry(
                    source_execution_id,
                    execution_id=new_execution_id(),
                    operation_id=operation_id,
                )
            )
            event_receipt = (
                self._append_retry_admission_event(
                    admission,
                    source=source,
                    operation_id=operation_id,
                )
            )
            audit_receipt = (
                self._append_retry_result_audit(
                    admission,
                    source_execution_id=(
                        source.execution_id
                    ),
                    operation_id=operation_id,
                    event_id=event_receipt.record_id,
                )
            )
            return RetryEventOutcome(
                admission_result=admission,
                admission_event_append_receipt=(
                    event_receipt
                ),
                audit_append_receipt=audit_receipt,
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
        admission_event_append_receipt = (
            self._append_retry_admission_event(
                admission,
                source=source,
                operation_id=operation_id,
            )
        )
        audit_append_receipt = (
            self._append_retry_result_audit(
                admission,
                source_execution_id=(
                    source.execution_id
                ),
                operation_id=operation_id,
                event_id=(
                    admission_event_append_receipt
                    .record_id
                ),
            )
        )

        if not admission.applied:
            return RetryEventOutcome(
                admission_result=admission,
                admission_event_append_receipt=(
                    admission_event_append_receipt
                ),
                audit_append_receipt=(
                    audit_append_receipt
                ),
            )

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

        event_append_receipt = (
            self._append_dispatch_event(
                work_id=source.work_id,
                task_id=source.task_id,
                execution_id=(
                    admission.execution.execution_id
                ),
                executor_id=(
                    dispatch_decision.executor_id
                ),
                runtime_id=(
                    dispatch_decision.runtime_id
                ),
                agent_id=dispatch_decision.agent_id,
                requested_agent_id=(
                    source.requested_agent_id
                ),
                required_capability=(
                    source.required_capability
                ),
                operation_id=operation_id,
            )
        )

        admission = replace(
            admission,
            event_append_receipt=(
                event_append_receipt
            ),
        )

        started.wait(timeout=0.1)

        return RetryEventOutcome(
            admission_result=admission,
            admission_event_append_receipt=(
                admission_event_append_receipt
            ),
            audit_append_receipt=(
                audit_append_receipt
            ),
        )

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

        try:
            dispatch_decision = (
                self.execution_dispatcher.dispatch(
                    DispatchRequest(
                        work_id=work_id,
                        task_id=task_id,
                        execution_id=execution_id,
                        command=command,
                        requested_agent_id=(
                            requested_agent_id
                        ),
                        required_capability=(
                            required_capability
                        ),
                    )
                )
            )
        except ValueError as error:
            audit_append_receipt = (
                self._append_submit_audit(
                    work_id=work_id,
                    outcome="rejected",
                    reason_code="dispatch_rejected",
                    error_code=type(error).__name__,
                )
            )
            raise AuditedDispatchRejectionError(
                str(error),
                reason_code="dispatch_rejected",
                audit_append_receipt=(
                    audit_append_receipt
                ),
            ) from error

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

        event_append_receipt = (
            self._append_dispatch_event(
                work_id=work_id,
                task_id=task_id,
                execution_id=execution_id,
                executor_id=(
                    dispatch_decision.executor_id
                ),
                runtime_id=(
                    dispatch_decision.runtime_id
                ),
                agent_id=dispatch_decision.agent_id,
                requested_agent_id=(
                    requested_agent_id
                ),
                required_capability=(
                    required_capability
                ),
                operation_id=(
                    f"{execution_id}:dispatch"
                ),
            )
        )

        audit_append_receipt = (
            self._append_submit_audit(
                work_id=work_id,
                outcome="accepted",
                reason_code="dispatch_accepted",
                event_id=event_append_receipt.record_id,
            )
        )

        started.wait(timeout=0.1)

        task = self.task_store.get(task_id)

        return {
            "status": "accepted",
            "work_id": work_id,
            "task_id": task_id,
            "execution_id": execution_id,
            "event_append_receipt": (
                event_append_receipt
            ),
            "audit_append_receipt": (
                audit_append_receipt
            ),
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

    def cancel_task(
        self,
        task_id: str,
        *,
        cancel_operation_id: str,
        cleanup_operation_id: str,
    ) -> dict[str, object]:
        if (
            not isinstance(cancel_operation_id, str)
            or not cancel_operation_id.strip()
        ):
            raise AuditedCancelError(
                "Cancel operation ID is required.",
                reason_code="invalid_cancel_operation_id",
                audit_append_receipt=None,
            )

        task = self.task_store.get(task_id)

        if task is None:
            raise self._cancel_rejection_error(
                "Task not found.",
                task_id=task_id,
                cancel_operation_id=(
                    cancel_operation_id
                ),
                reason_code="task_not_found",
            )

        executions = self.execution_registry.list_by_task(
            task_id
        )

        if not executions:
            raise self._cancel_rejection_error(
                "Execution not found.",
                task_id=task_id,
                cancel_operation_id=(
                    cancel_operation_id
                ),
                reason_code="execution_not_found",
            )

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
        cleanup_event_append_receipt = None
        cancel_applied = (
            transition.execution.status
            == ExecutionStatus.CANCELLED
            and transition.disposition
            in {
                TransitionDisposition.APPLIED,
                TransitionDisposition.IDEMPOTENT_REPLAY,
            }
        )

        if cancel_applied:
            cleanup_result = self._cleanup_process_ownership(
                task_id,
                expected_execution_id=(
                    execution.execution_id
                ),
            )
            cleanup_event_append_receipt = (
                self._append_cleanup_event(
                    cleanup_result,
                    task_id=task_id,
                    cleanup_operation_id=(
                        cleanup_operation_id
                    ),
                    trigger="cancel",
                    work_id=task.work_id,
                )
            )

        updated = self.task_store.get(task_id)

        response = (
            updated.to_dict()
            if updated
            else {
                "task_id": task_id,
                "status": (
                    transition.execution.status.value
                ),
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
        response["cleanup_event_append_receipt"] = (
            cleanup_event_append_receipt
        )

        transition_receipt = (
            transition.event_append_receipt
        )
        audit_receipt = self._append_cancel_audit(
            task_id=task_id,
            cancel_operation_id=cancel_operation_id,
            outcome=(
                "accepted"
                if cancel_applied
                else "rejected"
            ),
            reason_code=(
                "cancel_applied"
                if cancel_applied
                else "terminal_winner_preserved"
            ),
            event_id=(
                transition_receipt.record_id
                if transition_receipt
                else None
            ),
        )
        response["audit_append_receipt"] = (
            audit_receipt
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
        *,
        cleanup_operation_id: str,
    ) -> dict[str, CleanupEventOutcome]:
        """Clean ownership retained from an earlier session."""

        ownerships = self.process_registry.all()
        results: dict[str, CleanupEventOutcome] = {}

        for task_id, ownership in ownerships.items():
            cleanup_result = self._cleanup_process_ownership(
                task_id,
                expected_execution_id=(
                    ownership.execution_id
                ),
            )
            task = self.task_store.get(task_id)
            event_receipt = self._append_cleanup_event(
                cleanup_result,
                task_id=task_id,
                cleanup_operation_id=cleanup_operation_id,
                trigger="registered_cleanup",
                work_id=(
                    task.work_id
                    if task is not None
                    else None
                ),
            )
            results[task_id] = CleanupEventOutcome(
                cleanup_result=cleanup_result,
                event_append_receipt=event_receipt,
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
