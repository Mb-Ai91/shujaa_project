from __future__ import annotations

import importlib
import inspect
import logging

import pytest

import core.manager.service as service_module
from core.manager.service import ShujaaManager
from core.policy import contracts
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationDecision,
    AuthorizationEffect,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import SinglePrincipalCancelEvaluator
from core.tasks.store import InMemoryTaskStore
from core.work.dispatcher import DispatchDecision
from core.work.event_store import (
    AppendReceipt,
    InMemoryAuditStore,
    InMemoryEventStore,
)
from core.work.events import AppendResult
from core.work.execution_registry import InMemoryExecutionRegistry
from core.work.registry import InMemoryWorkRegistry


_UNSET = object()
_ACTOR = ActorRef(
    actor_type="service",
    actor_id="stage7-submit-local-api",
)
_POLICY_VERSION = "stage7.2-test-policy-v1"


class _UnusedRunner:
    def start(self, command):
        raise AssertionError("Runtime execution is not expected.")


class _Evaluator:
    def __init__(self, decision=None, error=None):
        self.decision = decision
        self.error = error
        self.requests = []

    def evaluate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.decision


class _Dispatcher:
    def __init__(self, *, reject=False, trace=None):
        self.reject = reject
        self.trace = trace
        self.requests = []

    def dispatch(self, request):
        self.requests.append(request)
        if self.trace is not None:
            self.trace.append("dispatch")
        if self.reject:
            raise ValueError("injected_submit_dispatch_rejection")
        return DispatchDecision(
            executor_id="stage7-submit-executor",
            runtime_id="stage7-submit-runtime",
        )


class _RecordingThread:
    starts = 0
    trace = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def start(self):
        type(self).starts += 1
        if type(self).trace is not None:
            type(self).trace.append("thread")


class _RecordingTaskStore(InMemoryTaskStore):
    def __init__(self, trace=None):
        super().__init__()
        self.trace = trace
        self.create_calls = 0

    def create(self, task):
        self.create_calls += 1
        if self.trace is not None:
            self.trace.append("task")
        return super().create(task)


class _RecordingWorkRegistry(InMemoryWorkRegistry):
    def __init__(self, trace=None):
        super().__init__()
        self.trace = trace
        self.create_calls = 0

    def create(self, work):
        self.create_calls += 1
        if self.trace is not None:
            self.trace.append("work")
        return super().create(work)


class _RecordingExecutionRegistry(InMemoryExecutionRegistry):
    def __init__(self, trace=None):
        super().__init__()
        self.trace = trace
        self.create_calls = 0

    def create(self, execution):
        self.create_calls += 1
        if self.trace is not None:
            self.trace.append("execution")
        return super().create(execution)


class _AuditStore:
    def __init__(
        self,
        *,
        authorization_mode=None,
        outcome_mode=None,
        trace=None,
    ):
        self._delegate = InMemoryAuditStore()
        self.authorization_mode = authorization_mode
        self.outcome_mode = outcome_mode
        self.trace = trace
        self.records = []
        self.authorization_attempts = 0

    @staticmethod
    def _is_authorization(record):
        return record.action == "authorization.work.submit"

    @staticmethod
    def _is_outcome(record):
        return record.action == "work.submit"

    @staticmethod
    def _write_failure(record):
        return AppendReceipt(
            result=AppendResult.WRITE_FAILED,
            record_id=record.audit_id,
            error_code="injected_stage7_submit_audit_failure",
        )

    def _append(self, record, *, replay_stable):
        self.records.append(record)
        if self._is_authorization(record):
            self.authorization_attempts += 1
            if self.trace is not None:
                self.trace.append("authorization_audit")
            mode = self.authorization_mode
            if mode == "write":
                return self._write_failure(record)
            if mode == "malformed":
                return object()
            if mode == "raise":
                raise RuntimeError(
                    "sensitive_pre_action_audit_error"
                )
            if mode == "ambiguous":
                self._delegate.append_replay_stable(record)
                raise RuntimeError(
                    "sensitive_ambiguous_append_outcome"
                )
        elif self._is_outcome(record):
            if self.trace is not None:
                self.trace.append("outcome_audit")
            mode = self.outcome_mode
            if mode == "write":
                return self._write_failure(record)
            if mode == "raise":
                raise RuntimeError(
                    "sensitive_post_action_audit_error"
                )

        if replay_stable:
            return self._delegate.append_replay_stable(record)
        return self._delegate.append(record)

    def append(self, record):
        return self._append(record, replay_stable=False)

    def append_replay_stable(self, record):
        return self._append(record, replay_stable=True)

    def get(self, record_id):
        return self._delegate.get(record_id)

    def list(self, after_sequence=0, limit=None):
        return self._delegate.list(after_sequence, limit)

    def verify_integrity(self):
        return self._delegate.verify_integrity()


@pytest.fixture(autouse=True)
def _isolate_threads(monkeypatch):
    _RecordingThread.starts = 0
    _RecordingThread.trace = None
    monkeypatch.setattr(service_module, "Thread", _RecordingThread)


def _decision(effect="ALLOW"):
    return AuthorizationDecision(
        effect=effect,
        reason_code=(
            "submit_allowed"
            if effect == "ALLOW"
            else "submit_denied"
        ),
        policy_version=_POLICY_VERSION,
    )


def _request(
    operation_id="op-stage7-submit",
    *,
    request_id=None,
    action="work.submit",
    resource_type="work_submission",
    resource_id=None,
):
    return AuthorizationRequest(
        actor=_ACTOR,
        action=action,
        resource=ResourceRef(
            resource_type=resource_type,
            resource_id=(resource_id or operation_id),
        ),
        context=AuthorizationContext(
            request_id=(
                request_id or f"request-{operation_id}"
            ),
            operation_id=operation_id,
        ),
    )


def _manager(
    *,
    evaluator=_UNSET,
    audit_store=None,
    dispatcher=None,
    trace=None,
):
    task_store = _RecordingTaskStore(trace)
    work_registry = _RecordingWorkRegistry(trace)
    execution_registry = _RecordingExecutionRegistry(trace)
    dispatcher = dispatcher or _Dispatcher(trace=trace)
    kwargs = {
        "crew_runner": _UnusedRunner(),
        "task_store": task_store,
        "work_registry": work_registry,
        "execution_registry": execution_registry,
        "event_store": InMemoryEventStore(),
        "audit_store": audit_store or _AuditStore(trace=trace),
        "execution_dispatcher": dispatcher,
    }
    if evaluator is not _UNSET:
        kwargs["submit_authorization_evaluator"] = evaluator
    try:
        manager = ShujaaManager(**kwargs)
    except TypeError as error:
        pytest.fail(
            "Slice 7.2 submit evaluator injection is missing: "
            f"{type(error).__name__}"
        )
    manager._stage7_test_dispatcher = dispatcher
    return manager


def _submit(manager, request, command="stage7 submit command"):
    parameters = inspect.signature(manager.submit).parameters
    assert "authorization_request" in parameters, (
        "Slice 7.2 requires authorization_request on Manager.submit"
    )
    assert "submit_operation_id" not in parameters, (
        "operation identity must come only from request.context"
    )
    return manager.submit(
        command,
        authorization_request=request,
    )


def _invoke(manager, request, command="stage7 submit command"):
    try:
        return _submit(manager, request, command)
    except Exception as error:
        return error


def _reason_code(outcome):
    if isinstance(outcome, dict):
        return outcome.get("error_code") or outcome.get("reason_code")
    return getattr(outcome, "reason_code", None)


def _snapshot(manager):
    return (
        len(manager._stage7_test_dispatcher.requests),
        manager.work_registry.create_calls,
        manager.task_store.create_calls,
        manager.execution_registry.create_calls,
        _RecordingThread.starts,
    )


def test_submit_contract_is_action_specific_and_signature_has_one_source():
    assert hasattr(contracts, "CancelAuthorizationEvaluatorProtocol")
    assert hasattr(contracts, "SubmitAuthorizationEvaluatorProtocol"), (
        "Slice 7.2 SubmitAuthorizationEvaluatorProtocol is missing"
    )
    assert not hasattr(contracts, "AuthorizationEvaluatorProtocol")

    parameters = inspect.signature(ShujaaManager.submit).parameters
    assert "authorization_request" in parameters
    assert "submit_operation_id" not in parameters


def test_canonical_operation_id_comes_from_request_context_and_audit():
    operation_id = "op-stage7-canonical-source"
    audit_store = _AuditStore()
    manager = _manager(
        evaluator=_Evaluator(_decision()),
        audit_store=audit_store,
    )

    response = _submit(manager, _request(operation_id))

    authorization_records = [
        record
        for record in audit_store.records
        if record.action == "authorization.work.submit"
    ]
    assert len(authorization_records) == 1
    record = authorization_records[0]
    assert record.operation_id == operation_id
    assert record.resource_type == "work_submission"
    assert record.resource_id == operation_id
    assert response["authorization_audit_append_receipt"].result is (
        AppendResult.APPENDED
    )


@pytest.mark.parametrize("mode", ("missing", "exception", "malformed"))
def test_unavailable_submit_evaluator_fails_closed(mode):
    if mode == "missing":
        manager = _manager()
    elif mode == "exception":
        manager = _manager(
            evaluator=_Evaluator(
                error=RuntimeError("sensitive_evaluator_error")
            )
        )
    else:
        manager = _manager(evaluator=_Evaluator(object()))

    outcome = _invoke(manager, _request(f"op-{mode}"))

    assert _reason_code(outcome) == "EVALUATOR_UNAVAILABLE"
    assert _snapshot(manager) == (0, 0, 0, 0, 0)


@pytest.mark.parametrize(
    ("authorization_request", "expected"),
    (
        (_request("op-invalid-action", action="task.cancel"), "AUTHORIZATION_REQUEST_INVALID"),
        (_request("op-invalid-resource", resource_type="task"), "AUTHORIZATION_REQUEST_INVALID"),
        (_request("op-invalid-binding", resource_id="other-operation"), "AUTHORIZATION_REQUEST_INVALID"),
    ),
)
def test_invalid_request_is_distinct_from_policy_deny(
    authorization_request, expected
):
    evaluator = _Evaluator(_decision())
    manager = _manager(evaluator=evaluator)

    outcome = _invoke(manager, authorization_request)

    assert _reason_code(outcome) == expected
    assert evaluator.requests == []
    assert _snapshot(manager) == (0, 0, 0, 0, 0)


def test_explicit_policy_deny_is_not_request_invalid():
    evaluator = _Evaluator(_decision("DENY"))
    manager = _manager(evaluator=evaluator)

    outcome = _invoke(manager, _request("op-policy-deny"))

    assert _reason_code(outcome) == "POLICY_DENIED"
    assert len(evaluator.requests) == 1
    assert _snapshot(manager) == (0, 0, 0, 0, 0)


@pytest.mark.parametrize("mode", ("write", "malformed", "raise"))
def test_pre_action_evidence_failure_blocks_every_side_effect(mode):
    audit_store = _AuditStore(authorization_mode=mode)
    manager = _manager(
        evaluator=_Evaluator(_decision()),
        audit_store=audit_store,
    )

    outcome = _invoke(manager, _request(f"op-audit-{mode}"))

    assert _reason_code(outcome) == "AUDIT_UNAVAILABLE"
    assert _snapshot(manager) == (0, 0, 0, 0, 0)


def test_pre_action_evidence_precedes_dispatch_and_all_mutations():
    trace = []
    audit_store = _AuditStore(trace=trace)
    dispatcher = _Dispatcher(trace=trace)
    manager = _manager(
        evaluator=_Evaluator(_decision()),
        audit_store=audit_store,
        dispatcher=dispatcher,
        trace=trace,
    )
    _RecordingThread.trace = trace

    response = _submit(manager, _request("op-order"))

    assert response["status"] == "accepted"
    assert trace[0] == "authorization_audit"
    assert trace.index("authorization_audit") < trace.index("dispatch")
    for side_effect in ("work", "task", "execution", "thread"):
        assert trace.index("authorization_audit") < trace.index(side_effect)


def test_appended_operation_replay_is_409_without_second_submission():
    manager = _manager(evaluator=_Evaluator(_decision()))
    request = _request("op-replay")

    first = _submit(manager, request)
    before = _snapshot(manager)
    second = _invoke(manager, request)

    assert first["status"] == "accepted"
    assert _reason_code(second) == "SUBMIT_OPERATION_REUSED"
    assert _snapshot(manager) == before
    assert not hasattr(second, "original_result")


def test_identity_conflict_is_409_without_second_submission():
    manager = _manager(evaluator=_Evaluator(_decision()))
    first_request = _request(
        "op-conflict",
        request_id="request-conflict-first",
    )
    conflicting_request = _request(
        "op-conflict",
        request_id="request-conflict-second",
    )

    _submit(manager, first_request)
    before = _snapshot(manager)
    outcome = _invoke(manager, conflicting_request)

    assert _reason_code(outcome) == "SUBMIT_OPERATION_REUSED"
    assert _snapshot(manager) == before


def test_dispatch_rejection_still_consumes_operation_id():
    dispatcher = _Dispatcher(reject=True)
    manager = _manager(
        evaluator=_Evaluator(_decision()),
        dispatcher=dispatcher,
    )
    request = _request("op-dispatch-rejected")

    first = _invoke(manager, request)
    second = _invoke(manager, request)

    assert _reason_code(first) == "dispatch_rejected"
    assert _reason_code(second) == "SUBMIT_OPERATION_REUSED"
    assert len(dispatcher.requests) == 1
    assert manager.work_registry.create_calls == 0


def test_new_operation_id_after_rejection_is_a_new_attempt():
    dispatcher = _Dispatcher(reject=True)
    manager = _manager(
        evaluator=_Evaluator(_decision()),
        dispatcher=dispatcher,
    )

    first = _invoke(manager, _request("op-reject-first"))
    second = _invoke(manager, _request("op-reject-second"))

    assert _reason_code(first) == "dispatch_rejected"
    assert _reason_code(second) == "dispatch_rejected"
    assert len(dispatcher.requests) == 2


def test_ambiguous_pre_action_outcome_never_retries_automatically():
    evaluator = _Evaluator(_decision())
    audit_store = _AuditStore(authorization_mode="ambiguous")
    manager = _manager(
        evaluator=evaluator,
        audit_store=audit_store,
    )

    outcome = _invoke(manager, _request("op-ambiguous"))

    assert _reason_code(outcome) == "AUDIT_UNAVAILABLE"
    assert audit_store.authorization_attempts == 1
    assert len(evaluator.requests) == 1
    assert _snapshot(manager) == (0, 0, 0, 0, 0)


def test_post_action_audit_write_failure_preserves_acceptance():
    audit_store = _AuditStore(outcome_mode="write")
    manager = _manager(
        evaluator=_Evaluator(_decision()),
        audit_store=audit_store,
    )

    response = _submit(manager, _request("op-post-write-failure"))

    assert response["status"] == "accepted"
    assert response["audit_append_receipt"].result is (
        AppendResult.WRITE_FAILED
    )
    assert _snapshot(manager) == (1, 1, 1, 1, 1)


def test_post_action_audit_exception_is_sanitized_and_preserves_result(
    caplog,
):
    secret_command = "raw-submit-payload-must-not-be-logged"
    audit_store = _AuditStore(outcome_mode="raise")
    manager = _manager(
        evaluator=_Evaluator(_decision()),
        audit_store=audit_store,
    )

    with caplog.at_level("WARNING", logger="core.manager.service"):
        response = _submit(
            manager,
            _request("op-post-exception"),
            secret_command,
        )

    assert response["status"] == "accepted"
    assert _snapshot(manager) == (1, 1, 1, 1, 1)
    diagnostics = [
        record
        for record in caplog.records
        if record.getMessage() == "post_action_audit_failed"
    ]
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.diagnostic_code == "POST_ACTION_AUDIT_FAILED"
    assert diagnostic.exception_type == "RuntimeError"
    assert diagnostic.operation_id == "op-post-exception"
    assert diagnostic.request_id == "request-op-post-exception"
    assert diagnostic.resource_type == "work"
    assert diagnostic.resource_id == response["work_id"]
    assert diagnostic.args == ()
    assert diagnostic.exc_info is None
    assert diagnostic.exc_text is None
    assert diagnostic.stack_info is None
    rendered = repr(diagnostic.__dict__)
    for forbidden in (
        "sensitive_post_action_audit_error",
        secret_command,
        "X-Shujaa-Key",
        "secret-api-key",
    ):
        assert forbidden not in rendered


def test_direct_manager_submit_without_authorization_fails_closed():
    manager = _manager(evaluator=_Evaluator(_decision()))

    try:
        outcome = manager.submit("direct bypass attempt")
    except Exception as error:
        outcome = error

    assert _reason_code(outcome) == "EVALUATOR_UNAVAILABLE"
    assert _snapshot(manager) == (0, 0, 0, 0, 0)


@pytest.mark.parametrize(
    ("path", "payload"),
    (
        ("/shujaa-task", {"command": "submit through api"}),
        ("/agents/research-agent/execute", {"task": "agent submit"}),
    ),
)
def test_both_api_submit_routes_pass_bound_authorization(
    monkeypatch,
    path,
    payload,
):
    api_key = "stage7-submit-api-key-must-not-be-actor"
    monkeypatch.setenv("SHUJAA_API_KEY", api_key)
    api_module = importlib.import_module("apps.api.app")

    class FakeManager:
        TASK_TIMEOUT_SECONDS = 1

        def __init__(self):
            self.calls = []

        def submit(self, command, **kwargs):
            self.calls.append((command, kwargs))
            return {
                "status": "accepted",
                "work_id": "work-api-submit",
                "task_id": "task-api-submit",
                "execution_id": "exec-api-submit",
            }

        def get_task(self, task_id):
            return {
                "status": "completed",
                "result": "completed result",
            }

    fake = FakeManager()
    monkeypatch.setattr(api_module, "manager", fake)
    client = api_module.app.test_client()

    response = client.post(
        path,
        headers={"X-Shujaa-Key": api_key},
        json=payload,
    )

    assert response.status_code in {200, 202}
    assert len(fake.calls) == 1
    kwargs = fake.calls[0][1]
    assert "authorization_request" in kwargs
    assert "submit_operation_id" not in kwargs
    request = kwargs["authorization_request"]
    assert request.actor == api_module.API_SERVICE_ACTOR
    assert request.action == "work.submit"
    assert request.resource.resource_type == "work_submission"
    assert request.resource.resource_id == request.context.operation_id
    assert api_key not in repr(request)


@pytest.mark.parametrize(
    ("reason_code", "expected_status"),
    (
        ("AUTHORIZATION_REQUEST_INVALID", 400),
        ("POLICY_DENIED", 403),
        ("SUBMIT_OPERATION_REUSED", 409),
        ("EVALUATOR_UNAVAILABLE", 503),
        ("AUDIT_UNAVAILABLE", 503),
    ),
)
def test_submit_api_maps_structured_authorization_failures(
    monkeypatch,
    reason_code,
    expected_status,
):
    monkeypatch.setenv("SHUJAA_API_KEY", "stage7-submit-api-key")
    api_module = importlib.import_module("apps.api.app")

    class SubmitError(ValueError):
        def __init__(self):
            super().__init__("Sanitized submit failure.")
            self.reason_code = reason_code

    class FakeManager:
        def submit(self, command, **kwargs):
            raise SubmitError()

    monkeypatch.setattr(api_module, "manager", FakeManager())
    client = api_module.app.test_client()

    response = client.post(
        "/shujaa-task",
        headers={"X-Shujaa-Key": "stage7-submit-api-key"},
        json={"command": "submit"},
    )

    assert response.status_code == expected_status


def test_submit_authorization_and_audit_exclude_payload_and_secrets():
    secret_command = "raw-command secret-api-key must stay private"
    audit_store = _AuditStore()
    request = _request("op-privacy")
    manager = _manager(
        evaluator=_Evaluator(_decision()),
        audit_store=audit_store,
    )

    _submit(manager, request, secret_command)

    rendered = repr((request, audit_store.records))
    assert secret_command not in rendered
    assert "secret-api-key" not in rendered
    assert "X-Shujaa-Key" not in rendered


def test_slice7_1_protocol_remains_separate_and_unchanged():
    evaluator = SinglePrincipalCancelEvaluator(
        principal=_ACTOR,
        policy_version="stage7.1-regression-guard",
    )
    request = AuthorizationRequest(
        actor=_ACTOR,
        action="task.cancel",
        resource=ResourceRef(
            resource_type="task",
            resource_id="task-stage7-regression",
        ),
        context=AuthorizationContext(
            request_id="request-stage7-regression",
            operation_id="operation-stage7-regression",
        ),
    )

    decision = evaluator.evaluate(request)

    assert decision.effect is AuthorizationEffect.ALLOW
    assert hasattr(contracts, "CancelAuthorizationEvaluatorProtocol")
    assert not hasattr(contracts, "AuthorizationEvaluatorProtocol")
    assert "cancel_operation_id" in inspect.signature(
        ShujaaManager.cancel_task
    ).parameters


def test_submit_reuse_has_no_recovery_or_result_lookup_contract():
    manager = _manager(evaluator=_Evaluator(_decision()))
    request = _request("op-no-recovery")

    _submit(manager, request)
    outcome = _invoke(manager, request)

    assert _reason_code(outcome) == "SUBMIT_OPERATION_REUSED"
    for forbidden_name in (
        "recover_submit",
        "retry_submit",
        "get_submit_result",
        "restore_submit_result",
    ):
        assert not hasattr(manager, forbidden_name)
