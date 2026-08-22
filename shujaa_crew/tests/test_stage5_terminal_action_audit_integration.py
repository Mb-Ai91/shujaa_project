from __future__ import annotations

import ast
from dataclasses import fields
from hashlib import sha256
import inspect
import json

import pytest

import core.manager.service as service_module
from core.manager.service import ShujaaManager
from core.tasks.store import TaskRecord
from core.work.event_store import (
    AppendReceipt,
    InMemoryAuditStore,
    InMemoryEventStore,
)
from core.work.events import AppendResult, AuditRecord, WorkEvent
from core.work.models import Execution, ExecutionStatus


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runtime execution is not expected.")


class FailingAuditStore:
    def append(self, record):
        return AppendReceipt(
            result=AppendResult.WRITE_FAILED,
            record_id=record.audit_id,
            error_code="injected_terminal_audit_write_failure",
        )

    def append_replay_stable(self, record):
        return self.append(record)

    def get(self, record_id):
        return None

    def list(self, after_sequence=0, limit=None):
        return ()


def _manager(*, event_store=None, audit_store=None):
    return ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=(event_store or InMemoryEventStore()),
        audit_store=(audit_store or InMemoryAuditStore()),
    )


def _seed_running(manager: ShujaaManager, suffix: str):
    work_id = f"work-terminal-audit-{suffix}"
    task_id = f"task-terminal-audit-{suffix}"
    execution_id = f"exec-terminal-audit-{suffix}"
    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=work_id,
            command="sensitive terminal command must not enter audit",
            status="queued",
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
    manager.task_store.update(task_id, status="running")
    return task_id, execution_id


def _expected_audit_id(operation_id: str, execution_id: str):
    material = json.dumps(
        [operation_id, execution_id],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"audit-execution-terminal-{sha256(material).hexdigest()}"


def _stored_audit(store, record_id):
    stored = store.get(record_id)
    assert stored is not None
    assert isinstance(stored.record, AuditRecord)
    return stored.record


def test_terminal_audit_outcome_wraps_transition_contract():
    outcome_type = getattr(
        service_module,
        "TerminalAuditOutcome",
        None,
    )
    assert outcome_type is not None
    assert [item.name for item in fields(outcome_type)] == [
        "transition",
        "audit_append_receipt",
    ]

    manager = _manager()
    task_id, execution_id = _seed_running(manager, "contract")
    transition = manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id=f"{execution_id}:completed-contract",
        result="contract result",
    )
    receipt = AppendReceipt(
        result=AppendResult.APPENDED,
        record_id="audit-terminal-contract",
    )
    outcome = outcome_type(
        transition=transition,
        audit_append_receipt=receipt,
    )

    assert outcome.transition is transition
    assert outcome.audit_append_receipt is receipt
    assert outcome.applied is transition.applied
    assert outcome.disposition is transition.disposition
    assert outcome.execution is transition.execution
    assert outcome.event_append_receipt is (
        transition.event_append_receipt
    )


@pytest.mark.parametrize(
    ("target_status", "action", "reason_code", "error", "result"),
    (
        (
            ExecutionStatus.COMPLETED,
            "execution.complete",
            "execution_completed",
            None,
            "sensitive raw terminal result",
        ),
        (
            ExecutionStatus.FAILED,
            "execution.fail",
            "execution_failed",
            "sensitive raw terminal error",
            None,
        ),
        (
            ExecutionStatus.TIMED_OUT,
            "execution.timeout",
            "execution_timed_out",
            "sensitive raw timeout detail",
            None,
        ),
    ),
)
def test_system_terminal_action_emits_minimal_linked_audit(
    target_status,
    action,
    reason_code,
    error,
    result,
):
    event_store = InMemoryEventStore()
    audit_store = InMemoryAuditStore()
    manager = _manager(
        event_store=event_store,
        audit_store=audit_store,
    )
    task_id, execution_id = _seed_running(
        manager,
        target_status.value,
    )
    operation_id = f"op-terminal-audit-{target_status.value}"

    outcome = manager._reconcile_system_terminal_execution(
        task_id,
        execution_id,
        target_status=target_status,
        operation_id=operation_id,
        error=error,
        result=result,
    )

    expected_id = _expected_audit_id(
        operation_id,
        execution_id,
    )
    assert outcome.execution.status is target_status
    assert outcome.audit_append_receipt.result is (
        AppendResult.APPENDED
    )
    assert outcome.audit_append_receipt.record_id == expected_id
    assert outcome.event_append_receipt is not None

    audit = _stored_audit(audit_store, expected_id)
    assert audit.action == action
    assert audit.actor_type == "system"
    assert audit.actor_id == "shujaa_manager"
    assert audit.resource_type == "execution"
    assert audit.resource_id == execution_id
    assert audit.operation_id == operation_id
    assert audit.event_id == outcome.event_append_receipt.record_id
    assert audit.outcome == "applied"
    assert audit.reason_code == reason_code
    rendered = repr(audit)
    assert "sensitive raw terminal result" not in rendered
    assert "sensitive raw terminal error" not in rendered
    assert "sensitive raw timeout detail" not in rendered

    assert isinstance(event_store.list()[-1].record, WorkEvent)
    assert isinstance(audit_store.list()[-1].record, AuditRecord)
    assert event_store is not audit_store


def test_terminal_audit_replay_is_stable_without_duplicate():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task_id, execution_id = _seed_running(manager, "replay")
    operation_id = "op-terminal-audit-replay"

    first = manager._reconcile_system_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id=operation_id,
        result="original winning result",
    )
    replay = manager._reconcile_system_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id=operation_id,
        result="replacement result must not win",
    )

    assert first.audit_append_receipt.result is AppendResult.APPENDED
    assert replay.disposition.value == "idempotent_replay"
    assert replay.audit_append_receipt.result is (
        AppendResult.IDEMPOTENT_REPLAY
    )
    assert first.audit_append_receipt.record_id == (
        replay.audit_append_receipt.record_id
    )
    assert replay.execution.result == "original winning result"
    assert len(audit_store.list()) == 1


def test_losing_timeout_is_audited_without_replacing_winner():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task_id, execution_id = _seed_running(manager, "losing-timeout")

    winner = manager._reconcile_system_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id="op-terminal-winner-completed",
        result="winning result",
    )
    losing = manager._reconcile_system_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.TIMED_OUT,
        operation_id="op-terminal-losing-timeout",
        error="raw losing timeout must not enter audit",
    )

    assert winner.execution.status is ExecutionStatus.COMPLETED
    assert losing.disposition.value == "conflicting_terminal_attempt"
    assert losing.execution.status is ExecutionStatus.COMPLETED
    task = manager.task_store.get(task_id)
    assert task is not None
    assert task.status == "completed"
    assert task.result == "winning result"
    audit = _stored_audit(
        audit_store,
        losing.audit_append_receipt.record_id,
    )
    assert audit.action == "execution.timeout"
    assert audit.outcome == "rejected"
    assert audit.reason_code == "conflicting_terminal_attempt"
    assert "raw losing timeout" not in repr(audit)
    assert len(audit_store.list()) == 2


def test_terminal_audit_identity_conflict_preserves_first_record():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task_id, execution_id = _seed_running(manager, "identity-conflict")
    operation_id = "op-terminal-audit-identity-conflict"

    first = manager._reconcile_system_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id=operation_id,
        result="winning result",
    )
    conflict = manager._reconcile_system_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id=operation_id,
        error="losing error",
    )

    assert first.audit_append_receipt.result is AppendResult.APPENDED
    assert conflict.audit_append_receipt.result is (
        AppendResult.IDENTITY_CONFLICT
    )
    assert first.audit_append_receipt.record_id == (
        conflict.audit_append_receipt.record_id
    )
    audit = _stored_audit(
        audit_store,
        first.audit_append_receipt.record_id,
    )
    assert audit.action == "execution.complete"
    assert audit.outcome == "applied"
    assert audit.reason_code == "execution_completed"
    assert len(audit_store.list()) == 1


def test_terminal_audit_write_failure_preserves_terminal_winner():
    manager = _manager(audit_store=FailingAuditStore())
    task_id, execution_id = _seed_running(manager, "write-failure")

    outcome = manager._reconcile_system_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id="op-terminal-audit-write-failure",
        error="winning execution error",
    )

    assert outcome.execution.status is ExecutionStatus.FAILED
    assert outcome.execution.error == "winning execution error"
    assert outcome.event_append_receipt.result is AppendResult.APPENDED
    assert outcome.audit_append_receipt.result is (
        AppendResult.WRITE_FAILED
    )
    assert outcome.audit_append_receipt.error_code == (
        "injected_terminal_audit_write_failure"
    )
    task = manager.task_store.get(task_id)
    assert task is not None
    assert task.status == "failed"
    assert task.error == "winning execution error"


def test_cancel_reconciliation_does_not_emit_terminal_action_audit():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task_id, execution_id = _seed_running(manager, "cancel-boundary")

    transition = manager._reconcile_terminal_execution(
        task_id,
        execution_id,
        target_status=ExecutionStatus.CANCELLED,
        operation_id="op-cancel-boundary",
    )

    assert transition.execution.status is ExecutionStatus.CANCELLED
    assert not hasattr(transition, "audit_append_receipt")
    assert audit_store.list() == ()


def test_runtime_terminal_call_sites_use_audited_wrapper():
    source = ast.parse(inspect.getsource(service_module))

    manager_class = next(
        node
        for node in source.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ShujaaManager"
    )
    methods = {
        node.name: node
        for node in manager_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    def call_names(method_name):
        return [
            node.func.attr
            for node in ast.walk(methods[method_name])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
        ]

    process_calls = call_names("_execute_task")
    agent_calls = call_names("_execute_agent_task")
    assert process_calls.count(
        "_reconcile_system_terminal_execution"
    ) == 4
    assert agent_calls.count(
        "_reconcile_system_terminal_execution"
    ) == 1
    assert "_reconcile_terminal_execution" not in process_calls
    assert "_reconcile_terminal_execution" not in agent_calls
