from __future__ import annotations

from dataclasses import fields
import json
from hashlib import sha256

import pytest

import core.manager.service as service_module
from core.manager.service import CleanupEventOutcome, ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import SinglePrincipalCancelEvaluator
from core.runtime.process_registry import ProcessRegistry
from core.runtime.process_registry_contract import (
    CleanupDisposition,
    CleanupResult,
    ProcessOwnership,
)
from core.tasks.store import TaskRecord
from core.work.event_store import (
    AppendReceipt,
    InMemoryAuditStore,
    InMemoryEventStore,
)
from core.work.events import AppendResult
from core.work.models import Execution, ExecutionStatus


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runtime execution is not expected.")


class FailingAuditStore:
    def __init__(self):
        self._delegate = InMemoryAuditStore()

    def append(self, record):
        if record.action == "process_ownership.cleanup":
            return AppendReceipt(
                result=AppendResult.WRITE_FAILED,
                record_id=record.audit_id,
                error_code="injected_cleanup_audit_write_failure",
            )
        return self._delegate.append(record)

    def append_replay_stable(self, record):
        if record.action == "process_ownership.cleanup":
            return self.append(record)
        return self._delegate.append_replay_stable(record)

    def get(self, record_id):
        return self._delegate.get(record_id)

    def list(self, after_sequence=0, limit=None):
        return self._delegate.list(after_sequence, limit)


_CANCEL_ACTOR = ActorRef(
    actor_type="service",
    actor_id="test-cleanup-audit-local-api",
)
_CANCEL_EVALUATOR = SinglePrincipalCancelEvaluator(
    principal=_CANCEL_ACTOR,
    policy_version="test-cleanup-audit-v1",
)


def _authorized_cancel(
    manager,
    task_id,
    *,
    cancel_operation_id,
    cleanup_operation_id,
):
    return manager.cancel_task(
        task_id,
        authorization_request=AuthorizationRequest(
            actor=_CANCEL_ACTOR,
            action="task.cancel",
            resource=ResourceRef(
                resource_type="task",
                resource_id=task_id,
            ),
            context=AuthorizationContext(
                request_id=f"request-{cancel_operation_id}",
                operation_id=cancel_operation_id,
            ),
        ),
        cancel_operation_id=cancel_operation_id,
        cleanup_operation_id=cleanup_operation_id,
    )


def _ownership(
    task_id: str,
    *,
    execution_id: str = "exec-cleanup-audit",
) -> ProcessOwnership:
    return ProcessOwnership(
        task_id=task_id,
        execution_id=execution_id,
        pid=8101,
        pgid=8201,
        process_start_time_ticks=8301,
    )


def _seed_running_owner(
    manager: ShujaaManager,
    registry: ProcessRegistry,
    *,
    task_id: str,
    execution_id: str,
    work_id: str,
) -> None:
    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=work_id,
            command="sensitive cleanup command must not enter audit",
            status="running",
            error="sensitive cleanup error must not enter audit",
            process_id=8101,
            process_group_id=8201,
        )
    )
    manager.execution_registry.create(
        Execution(
            execution_id=execution_id,
            work_id=work_id,
            task_id=task_id,
        )
    )
    manager._transition_execution(
        execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id=f"{execution_id}:running",
    )
    registry.register(
        _ownership(
            task_id,
            execution_id=execution_id,
        )
    )


def _manager(
    *,
    process_registry=None,
    event_store=None,
    audit_store=None,
) -> ShujaaManager:
    return ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=process_registry,
        event_store=(event_store or InMemoryEventStore()),
        audit_store=(audit_store or InMemoryAuditStore()),
        cancel_authorization_evaluator=_CANCEL_EVALUATOR,
    )


def _expected_audit_id(
    cleanup_operation_id: str,
    task_id: str,
) -> str:
    material = json.dumps(
        [cleanup_operation_id, task_id],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return (
        "audit-process-ownership-cleanup-"
        f"{sha256(material).hexdigest()}"
    )


def _stored_audit(store, record_id):
    stored = store.get(record_id)
    assert stored is not None
    return stored.record


def test_cleanup_audit_outcome_wraps_existing_event_contract():
    outcome_type = getattr(
        service_module,
        "CleanupAuditOutcome",
        None,
    )

    assert outcome_type is not None
    assert [item.name for item in fields(outcome_type)] == [
        "cleanup_event_outcome",
        "audit_append_receipt",
    ]
    assert [item.name for item in fields(CleanupEventOutcome)] == [
        "cleanup_result",
        "event_append_receipt",
    ]

    cleanup_result = CleanupResult(
        disposition=CleanupDisposition.NOT_OWNED,
        ownership=None,
    )
    event_receipt = AppendReceipt(
        result=AppendResult.APPENDED,
        record_id="event-cleanup-audit-contract",
    )
    audit_receipt = AppendReceipt(
        result=AppendResult.APPENDED,
        record_id="audit-cleanup-audit-contract",
    )
    event_outcome = CleanupEventOutcome(
        cleanup_result=cleanup_result,
        event_append_receipt=event_receipt,
    )
    outcome = outcome_type(
        cleanup_event_outcome=event_outcome,
        audit_append_receipt=audit_receipt,
    )

    assert outcome.cleanup_result is cleanup_result
    assert outcome.event_append_receipt is event_receipt
    assert outcome.audit_append_receipt is audit_receipt
    assert outcome.disposition is cleanup_result.disposition
    assert outcome.ownership is cleanup_result.ownership
    assert outcome.error is cleanup_result.error


@pytest.mark.parametrize(
    ("disposition", "expected_outcome"),
    (
        (CleanupDisposition.TERMINATED_AND_RELEASED, "released"),
        (CleanupDisposition.ALREADY_EXITED_AND_RELEASED, "released"),
        (CleanupDisposition.NOT_OWNED, "no_effect"),
        (CleanupDisposition.OWNER_MISMATCH, "retained"),
        (CleanupDisposition.IDENTITY_MISMATCH, "retained"),
        (CleanupDisposition.PROCESS_GROUP_MISMATCH, "retained"),
        (
            CleanupDisposition.IDENTITY_CHECK_FAILED_RETAINED,
            "retained",
        ),
        (
            CleanupDisposition.TERMINATION_FAILED_RETAINED,
            "retained",
        ),
    ),
)
def test_cleanup_audit_is_minimal_linked_for_all_dispositions(
    disposition,
    expected_outcome,
):
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task_id = f"task-cleanup-audit-{disposition.value}"
    operation_id = f"op-cleanup-audit-{disposition.value}"
    cleanup_result = CleanupResult(
        disposition=disposition,
        ownership=(
            None
            if disposition is CleanupDisposition.NOT_OWNED
            else _ownership(task_id)
        ),
        error=(
            "sensitive raw cleanup failure"
            if disposition
            in {
                CleanupDisposition.IDENTITY_CHECK_FAILED_RETAINED,
                CleanupDisposition.TERMINATION_FAILED_RETAINED,
            }
            else None
        ),
    )
    event_receipt = manager._append_cleanup_event(
        cleanup_result,
        task_id=task_id,
        cleanup_operation_id=operation_id,
        trigger="registered_cleanup",
        work_id=f"work-{task_id}",
    )

    receipt = manager._append_cleanup_audit(
        cleanup_result,
        task_id=task_id,
        cleanup_operation_id=operation_id,
        event_id=event_receipt.record_id,
    )

    expected_id = _expected_audit_id(operation_id, task_id)
    assert receipt.result is AppendResult.APPENDED
    assert receipt.record_id == expected_id
    audit = _stored_audit(audit_store, expected_id)
    assert audit.action == "process_ownership.cleanup"
    assert audit.actor_type == "system"
    assert audit.actor_id == "shujaa_manager"
    assert audit.resource_type == "process_ownership"
    assert audit.resource_id == task_id
    assert audit.operation_id == operation_id
    assert audit.event_id == event_receipt.record_id
    assert audit.outcome == expected_outcome
    assert audit.reason_code == disposition.value
    rendered = repr(audit)
    assert "sensitive raw cleanup failure" not in rendered
    assert "8101" not in rendered
    assert "8201" not in rendered
    assert "8301" not in rendered


def test_cancel_exposes_separate_cleanup_audit_receipt(
    tmp_path,
    monkeypatch,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    audit_store = InMemoryAuditStore()
    manager = _manager(
        process_registry=registry,
        audit_store=audit_store,
    )
    task_id = "task-cancel-cleanup-audit"
    execution_id = "exec-cancel-cleanup-audit"
    operation_id = "op-cancel-cleanup-audit"
    _seed_running_owner(
        manager,
        registry,
        task_id=task_id,
        execution_id=execution_id,
        work_id="work-cancel-cleanup-audit",
    )
    manager._read_process_start_time_ticks = lambda pid: 8301
    monkeypatch.setattr(
        service_module.os,
        "getpgid",
        lambda pid: 8201,
    )
    manager._terminate_process_group_by_id = lambda pgid: None

    response = _authorized_cancel(
        manager,
        task_id,
        cancel_operation_id="op-cancel-request-cleanup-audit",
        cleanup_operation_id=operation_id,
    )

    receipt = response["cleanup_audit_append_receipt"]
    assert receipt.result is AppendResult.APPENDED
    assert receipt.record_id != response["audit_append_receipt"].record_id
    audit = _stored_audit(audit_store, receipt.record_id)
    assert audit.operation_id == operation_id
    assert audit.event_id == (
        response["cleanup_event_append_receipt"].record_id
    )
    assert audit.reason_code == "terminated_and_released"
    assert len(audit_store.list()) == 3


def test_registered_cleanup_exposes_audited_outcome(
    tmp_path,
    monkeypatch,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    audit_store = InMemoryAuditStore()
    manager = _manager(
        process_registry=registry,
        audit_store=audit_store,
    )
    task_id = "task-registered-cleanup-audit"
    execution_id = "exec-registered-cleanup-audit"
    operation_id = "op-registered-cleanup-audit"
    _seed_running_owner(
        manager,
        registry,
        task_id=task_id,
        execution_id=execution_id,
        work_id="work-registered-cleanup-audit",
    )
    manager._read_process_start_time_ticks = lambda pid: 8301
    monkeypatch.setattr(
        service_module.os,
        "getpgid",
        lambda pid: 8201,
    )
    manager._terminate_process_group_by_id = lambda pgid: None

    outcome = manager.cleanup_registered_processes(
        cleanup_operation_id=operation_id,
    )[task_id]

    assert type(outcome).__name__ == "CleanupAuditOutcome"
    assert outcome.cleanup_result.disposition is (
        CleanupDisposition.TERMINATED_AND_RELEASED
    )
    assert outcome.event_append_receipt.result is (
        AppendResult.APPENDED
    )
    assert outcome.audit_append_receipt.result is (
        AppendResult.APPENDED
    )
    audit = _stored_audit(
        audit_store,
        outcome.audit_append_receipt.record_id,
    )
    assert audit.event_id == outcome.event_append_receipt.record_id
    assert audit.operation_id == operation_id


def test_cleanup_audit_write_failure_does_not_change_cancel(
    tmp_path,
    monkeypatch,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = _manager(
        process_registry=registry,
        audit_store=FailingAuditStore(),
    )
    task_id = "task-cancel-cleanup-audit-failure"
    execution_id = "exec-cancel-cleanup-audit-failure"
    _seed_running_owner(
        manager,
        registry,
        task_id=task_id,
        execution_id=execution_id,
        work_id="work-cancel-cleanup-audit-failure",
    )
    manager._read_process_start_time_ticks = lambda pid: 8301
    monkeypatch.setattr(
        service_module.os,
        "getpgid",
        lambda pid: 8201,
    )
    manager._terminate_process_group_by_id = lambda pgid: None

    response = _authorized_cancel(
        manager,
        task_id,
        cancel_operation_id="op-cancel-request-audit-failure",
        cleanup_operation_id="op-cancel-cleanup-audit-failure",
    )

    assert response["status"] == "cancelled"
    assert response["cleanup_disposition"] == (
        CleanupDisposition.TERMINATED_AND_RELEASED.value
    )
    assert response["cleanup_event_append_receipt"].result is (
        AppendResult.APPENDED
    )
    receipt = response["cleanup_audit_append_receipt"]
    assert receipt.result is AppendResult.WRITE_FAILED
    assert receipt.error_code == (
        "injected_cleanup_audit_write_failure"
    )
    assert registry.get(task_id) is None
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )


def test_cleanup_audit_write_failure_does_not_change_bulk_cleanup(
    tmp_path,
    monkeypatch,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = _manager(
        process_registry=registry,
        audit_store=FailingAuditStore(),
    )
    task_id = "task-bulk-cleanup-audit-failure"
    execution_id = "exec-bulk-cleanup-audit-failure"
    _seed_running_owner(
        manager,
        registry,
        task_id=task_id,
        execution_id=execution_id,
        work_id="work-bulk-cleanup-audit-failure",
    )
    manager._read_process_start_time_ticks = lambda pid: 8301
    monkeypatch.setattr(
        service_module.os,
        "getpgid",
        lambda pid: 8201,
    )
    manager._terminate_process_group_by_id = lambda pgid: None

    outcome = manager.cleanup_registered_processes(
        cleanup_operation_id="op-bulk-cleanup-audit-failure",
    )[task_id]

    assert outcome.cleanup_result.disposition is (
        CleanupDisposition.TERMINATED_AND_RELEASED
    )
    assert outcome.event_append_receipt.result is (
        AppendResult.APPENDED
    )
    assert outcome.audit_append_receipt.result is (
        AppendResult.WRITE_FAILED
    )
    assert registry.get(task_id) is None
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.RUNNING
    )


def test_cleanup_audit_replay_is_stable_without_duplicate():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task_id = "task-cleanup-audit-replay"
    operation_id = "op-cleanup-audit-replay"
    cleanup_result = CleanupResult(
        disposition=CleanupDisposition.NOT_OWNED,
        ownership=None,
    )

    first = manager._append_cleanup_audit(
        cleanup_result,
        task_id=task_id,
        cleanup_operation_id=operation_id,
        event_id="event-cleanup-audit-replay",
    )
    replay = manager._append_cleanup_audit(
        cleanup_result,
        task_id=task_id,
        cleanup_operation_id=operation_id,
        event_id="event-cleanup-audit-replay",
    )

    assert first.result is AppendResult.APPENDED
    assert replay.result is AppendResult.IDEMPOTENT_REPLAY
    assert first.record_id == replay.record_id
    assert len(audit_store.list()) == 1


def test_cleanup_audit_identity_conflict_preserves_first_record():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task_id = "task-cleanup-audit-conflict"
    operation_id = "op-cleanup-audit-conflict"
    first_result = CleanupResult(
        disposition=CleanupDisposition.NOT_OWNED,
        ownership=None,
    )
    conflicting_result = CleanupResult(
        disposition=CleanupDisposition.OWNER_MISMATCH,
        ownership=_ownership(task_id),
    )

    first = manager._append_cleanup_audit(
        first_result,
        task_id=task_id,
        cleanup_operation_id=operation_id,
        event_id="event-cleanup-audit-conflict",
    )
    conflict = manager._append_cleanup_audit(
        conflicting_result,
        task_id=task_id,
        cleanup_operation_id=operation_id,
        event_id="event-cleanup-audit-conflict",
    )

    assert first.result is AppendResult.APPENDED
    assert conflict.result is AppendResult.IDENTITY_CONFLICT
    assert first.record_id == conflict.record_id
    stored = _stored_audit(audit_store, first.record_id)
    assert stored.reason_code == CleanupDisposition.NOT_OWNED.value
    assert len(audit_store.list()) == 1
