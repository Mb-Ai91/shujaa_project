from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
import importlib
import inspect
from pathlib import Path

import pytest

from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationDecision,
    AuthorizationEffect,
    AuthorizationRequest,
    CancelAuthorizationEvaluatorProtocol,
    ResourceRef,
    SubmitAuthorizationEvaluatorProtocol,
)
from core.policy.evaluator import (
    SinglePrincipalCancelEvaluator,
)
from core.work.event_store import (
    AppendReceipt,
    InMemoryAuditStore,
)
from core.work.events import AppendResult


_ACTOR = ActorRef(
    actor_type="service",
    actor_id="stage7.3-local-api-service",
)
_POLICY_VERSION = "stage7.3-runtime-control-v1"
_ACTIONS = (
    "execution.pause",
    "execution.resume",
    "execution.terminate",
)
_UNSET = object()


class _EvaluatorDouble:
    def __init__(self, decision=None, error=None):
        self.decision = decision
        self.error = error
        self.requests = []

    def evaluate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.decision


class _AuditStoreDouble:
    def __init__(self, mode="delegate"):
        self.mode = mode
        self.delegate = InMemoryAuditStore()
        self.records = []
        self.append_attempts = 0

    def append(self, record):
        raise AssertionError(
            "Runtime-control evidence must use replay-stable append."
        )

    def append_replay_stable(self, record):
        self.append_attempts += 1
        self.records.append(record)

        if self.mode == "raise":
            raise RuntimeError(
                "sensitive audit exception must not escape"
            )
        if self.mode == "ambiguous":
            self.delegate.append_replay_stable(record)
            raise RuntimeError(
                "sensitive ambiguous outcome must not retry"
            )
        if self.mode == "malformed":
            return object()
        if self.mode in {
            "write_failed",
            "replay",
            "conflict",
        }:
            result = {
                "write_failed": AppendResult.WRITE_FAILED,
                "replay": AppendResult.IDEMPOTENT_REPLAY,
                "conflict": AppendResult.IDENTITY_CONFLICT,
            }[self.mode]
            return AppendReceipt(
                result=result,
                record_id=record.audit_id,
                error_code="injected_non_success",
            )

        return self.delegate.append_replay_stable(record)

    def verify_integrity(self):
        return self.delegate.verify_integrity()

    def get(self, record_id):
        return self.delegate.get(record_id)

    def list(self, after_sequence=0, limit=None):
        return self.delegate.list(after_sequence, limit)


class _FutureStage8ConsumerDouble:
    """Test-only consumer; it is not a Runtime contract or adapter."""

    def __init__(self, gate):
        self.gate = gate
        self.downstream_calls = []
        self.observed_authorization = None

    def request_control(self, request):
        decision = self.gate.authorize(request)
        self.observed_authorization = decision
        self.downstream_calls.append(
            (request.action, request.resource.resource_id)
        )
        return decision


def _runtime_module():
    try:
        return importlib.import_module(
            "core.policy.runtime_control"
        )
    except ModuleNotFoundError as error:
        if error.name != "core.policy.runtime_control":
            raise
        pytest.fail(
            "Slice 7.3 runtime-control authorization gate "
            "is not implemented.",
            pytrace=False,
        )


def _runtime_evaluator_type():
    module = importlib.import_module("core.policy.evaluator")
    evaluator_type = getattr(
        module,
        "SinglePrincipalRuntimeControlEvaluator",
        None,
    )
    if evaluator_type is None:
        pytest.fail(
            "SinglePrincipalRuntimeControlEvaluator is missing.",
            pytrace=False,
        )
    return evaluator_type


def _runtime_protocol_type():
    module = importlib.import_module("core.policy.contracts")
    protocol_type = getattr(
        module,
        "RuntimeControlAuthorizationEvaluatorProtocol",
        None,
    )
    if protocol_type is None:
        pytest.fail(
            "RuntimeControlAuthorizationEvaluatorProtocol is missing.",
            pytrace=False,
        )
    return protocol_type


def _request(
    *,
    action="execution.pause",
    execution_id="execution-stage7.3-one",
    request_id="request-stage7.3-one",
    operation_id="operation-stage7.3-one",
    actor=_ACTOR,
    resource_type="execution",
):
    return AuthorizationRequest(
        actor=actor,
        action=action,
        resource=ResourceRef(
            resource_type=resource_type,
            resource_id=execution_id,
        ),
        context=AuthorizationContext(
            request_id=request_id,
            operation_id=operation_id,
        ),
    )


def _decision(effect=AuthorizationEffect.ALLOW):
    return AuthorizationDecision(
        effect=effect,
        reason_code=(
            "runtime_control_allowed"
            if effect is AuthorizationEffect.ALLOW
            else "runtime_control_denied"
        ),
        policy_version=_POLICY_VERSION,
    )


def _gate(*, evaluator=_UNSET, audit_store=_UNSET):
    module = _runtime_module()
    gate_type = getattr(
        module,
        "RuntimeControlAuthorizationGate",
        None,
    )
    if gate_type is None:
        pytest.fail(
            "RuntimeControlAuthorizationGate is missing.",
            pytrace=False,
        )

    if evaluator is _UNSET:
        evaluator = _EvaluatorDouble(_decision())
    if audit_store is _UNSET:
        audit_store = _AuditStoreDouble()

    return gate_type(
        evaluator=evaluator,
        audit_store=audit_store,
    )


def _invoke(gate, request):
    try:
        return gate.authorize(request)
    except Exception as error:
        return error


def _reason_code(outcome):
    return getattr(outcome, "reason_code", None)


def test_contracts_and_runtime_evaluator_are_immutable_and_validate():
    actor = _ACTOR
    request = _request()
    decision = _decision()

    for value, attribute in (
        (actor, "actor_id"),
        (request.resource, "resource_id"),
        (request.context, "operation_id"),
        (request, "action"),
        (decision, "policy_version"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(value, attribute, "changed")

    evaluator_type = _runtime_evaluator_type()
    evaluator = evaluator_type(
        principal=_ACTOR,
        policy_version=_POLICY_VERSION,
    )
    with pytest.raises(FrozenInstanceError):
        evaluator.policy_version = "changed"
    with pytest.raises(ValueError):
        evaluator_type(principal=_ACTOR, policy_version=" ")


@pytest.mark.parametrize("action", _ACTIONS)
def test_exact_runtime_control_actions_and_execution_resource(action):
    evaluator_type = _runtime_evaluator_type()
    evaluator = evaluator_type(
        principal=_ACTOR,
        policy_version=_POLICY_VERSION,
    )

    allowed = evaluator.evaluate(_request(action=action))
    wrong_action = evaluator.evaluate(
        _request(action="task.cancel")
    )
    wrong_resource = evaluator.evaluate(
        _request(action=action, resource_type="task")
    )

    assert allowed.effect is AuthorizationEffect.ALLOW
    assert wrong_action.effect is AuthorizationEffect.DENY
    assert wrong_resource.effect is AuthorizationEffect.DENY


def test_action_specific_protocol_is_separate_from_7_1_and_7_2():
    protocol_type = _runtime_protocol_type()

    assert protocol_type is not CancelAuthorizationEvaluatorProtocol
    assert protocol_type is not SubmitAuthorizationEvaluatorProtocol
    assert inspect.signature(protocol_type.evaluate) == (
        inspect.signature(
            CancelAuthorizationEvaluatorProtocol.evaluate
        )
    )

    evaluator_module = importlib.import_module(
        "core.policy.evaluator"
    )
    assert not hasattr(
        evaluator_module,
        "GeneralAuthorizationEvaluator",
    )
    assert not hasattr(
        evaluator_module,
        "SystemAuthorizationEvaluator",
    )


def test_gate_uses_authorization_context_as_only_operation_id_source():
    gate = _gate()
    parameters = inspect.signature(gate.authorize).parameters

    assert tuple(parameters) == ("request",)
    request = _request(operation_id="canonical-operation")
    decision = gate.authorize(request)
    assert decision.effect is AuthorizationEffect.ALLOW


@pytest.mark.parametrize(
    ("evaluator", "expected"),
    (
        (None, "EVALUATOR_UNAVAILABLE"),
        (
            _EvaluatorDouble(error=RuntimeError("sensitive")),
            "EVALUATOR_UNAVAILABLE",
        ),
        (_EvaluatorDouble(decision=object()), "EVALUATOR_UNAVAILABLE"),
        (
            _EvaluatorDouble(
                decision=type(
                    "UnknownDecision",
                    (),
                    {
                        "effect": "UNKNOWN",
                        "reason_code": "unknown",
                        "policy_version": "v1",
                    },
                )()
            ),
            "EVALUATOR_UNAVAILABLE",
        ),
        (
            _EvaluatorDouble(
                decision=_decision(AuthorizationEffect.DENY)
            ),
            "POLICY_DENIED",
        ),
    ),
)
def test_evaluator_failures_and_deny_fail_closed(evaluator, expected):
    audit_store = _AuditStoreDouble()
    gate = _gate(
        evaluator=evaluator,
        audit_store=audit_store,
    )

    outcome = _invoke(gate, _request())

    assert _reason_code(outcome) == expected
    assert audit_store.append_attempts == 0


@pytest.mark.parametrize(
    "candidate",
    (
        _request(action="task.cancel"),
        _request(resource_type="task"),
        _decision(),
    ),
)
def test_invalid_action_resource_or_request_binding_is_rejected(
    candidate,
):
    gate = _gate()

    outcome = _invoke(gate, candidate)

    assert _reason_code(outcome) == "AUTHORIZATION_REQUEST_INVALID"


@pytest.mark.parametrize(
    "mode",
    (
        "raise",
        "malformed",
        "write_failed",
        "replay",
        "conflict",
    ),
)
def test_missing_or_non_success_audit_evidence_fails_closed(mode):
    audit_store = _AuditStoreDouble(mode)
    gate = _gate(audit_store=audit_store)

    outcome = _invoke(gate, _request())

    assert _reason_code(outcome) == "AUDIT_UNAVAILABLE"
    assert audit_store.append_attempts == 1


def test_missing_audit_store_fails_closed():
    gate = _gate(audit_store=None)

    outcome = _invoke(gate, _request())

    assert _reason_code(outcome) == "AUDIT_UNAVAILABLE"


def test_appended_evidence_contains_minimum_linkage_and_no_secrets():
    audit_store = _AuditStoreDouble()
    gate = _gate(audit_store=audit_store)
    request = _request(
        action="execution.resume",
        execution_id="execution-linkage",
        request_id="request-linkage",
        operation_id="operation-linkage",
    )

    decision = gate.authorize(request)

    assert decision.effect is AuthorizationEffect.ALLOW
    assert len(audit_store.records) == 1
    record = audit_store.records[0]
    assert record.actor_type == _ACTOR.actor_type
    assert record.actor_id == _ACTOR.actor_id
    assert record.action == "authorization.execution.resume"
    assert record.resource_type == "execution"
    assert record.resource_id == "execution-linkage"
    assert record.request_id == "request-linkage"
    assert record.operation_id == "operation-linkage"
    assert record.policy_version == _POLICY_VERSION

    serialized = repr(record).lower()
    for forbidden in (
        "api_key",
        "credential",
        "raw payload",
        "raw command",
        "secret-value",
        "traceback",
    ):
        assert forbidden not in serialized


def test_cross_action_execution_and_operation_reuse_are_not_authorized():
    audit_store = _AuditStoreDouble()
    gate = _gate(audit_store=audit_store)
    first = _request(
        action="execution.pause",
        execution_id="execution-one",
        request_id="request-one",
        operation_id="shared-operation",
    )

    assert gate.authorize(first).effect is AuthorizationEffect.ALLOW

    for reused in (
        _request(
            action="execution.resume",
            execution_id="execution-one",
            request_id="request-two",
            operation_id="shared-operation",
        ),
        _request(
            action="execution.pause",
            execution_id="execution-two",
            request_id="request-three",
            operation_id="shared-operation",
        ),
        first,
    ):
        assert _reason_code(_invoke(gate, reused)) == (
            "AUDIT_UNAVAILABLE"
        )

    fresh = _request(
        action="execution.resume",
        execution_id="execution-one",
        request_id="request-fresh",
        operation_id="fresh-operation",
    )
    assert gate.authorize(fresh).effect is AuthorizationEffect.ALLOW


def test_no_transferable_permit_registry_or_previous_decision_input():
    module = _runtime_module()
    public_names = {
        name.lower()
        for name in vars(module)
        if not name.startswith("_")
    }

    assert not any("permit" in name for name in public_names)
    assert not any("token" in name for name in public_names)
    assert not any("registry" in name for name in public_names)

    outcome = _invoke(_gate(), _decision())
    assert _reason_code(outcome) == "AUTHORIZATION_REQUEST_INVALID"


def test_ambiguous_audit_outcome_is_not_retried_automatically():
    audit_store = _AuditStoreDouble("ambiguous")
    gate = _gate(audit_store=audit_store)

    outcome = _invoke(gate, _request())

    assert _reason_code(outcome) == "AUDIT_UNAVAILABLE"
    assert audit_store.append_attempts == 1


def test_test_only_future_consumer_does_not_call_downstream_on_failure():
    consumer = _FutureStage8ConsumerDouble(
        _gate(
            evaluator=_EvaluatorDouble(
                _decision(AuthorizationEffect.DENY)
            )
        )
    )

    outcome = _invoke(consumer.gate, _request())

    assert _reason_code(outcome) == "POLICY_DENIED"
    assert consumer.downstream_calls == []
    assert consumer.observed_authorization is None


def test_test_only_future_consumer_can_observe_same_scenario_success():
    consumer = _FutureStage8ConsumerDouble(_gate())
    request = _request(action="execution.terminate")

    decision = consumer.request_control(request)

    assert decision.effect is AuthorizationEffect.ALLOW
    assert consumer.observed_authorization is decision
    assert consumer.downstream_calls == [
        ("execution.terminate", "execution-stage7.3-one")
    ]


def test_allow_exposes_no_runtime_support_or_lifecycle_claim():
    decision = _gate().authorize(_request())

    assert isinstance(decision, AuthorizationDecision)
    assert not hasattr(decision, "runtime_supported")
    assert not hasattr(decision, "lifecycle_eligible")
    assert not hasattr(decision, "execution_status")
    assert not hasattr(decision, "action_executed")


def test_execution_terminate_is_not_task_cancel_authorization():
    cancel_evaluator = SinglePrincipalCancelEvaluator(
        principal=_ACTOR,
        policy_version="stage7.1-existing-policy",
    )
    terminate_request = _request(action="execution.terminate")

    assert (
        cancel_evaluator.evaluate(terminate_request).effect
        is AuthorizationEffect.DENY
    )
    assert (
        _runtime_evaluator_type()(
            principal=_ACTOR,
            policy_version=_POLICY_VERSION,
        ).evaluate(terminate_request).effect
        is AuthorizationEffect.ALLOW
    )


def test_stage7_3_production_boundary_has_no_runtime_integration():
    project_root = Path(__file__).resolve().parents[1]
    policy_root = project_root / "core" / "policy"
    forbidden_import_roots = {
        "adapters",
        "core.manager",
        "core.runtime",
        "os",
        "signal",
        "subprocess",
    }
    forbidden_class_tokens = {
        "adapter",
        "fake",
        "runner",
        "stub",
    }

    for path in policy_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(
                        alias.name == root
                        or alias.name.startswith(f"{root}.")
                        for root in forbidden_import_roots
                    )
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not any(
                    module == root
                    or module.startswith(f"{root}.")
                    for root in forbidden_import_roots
                )
            if isinstance(node, ast.ClassDef):
                lowered = node.name.lower()
                assert not any(
                    token in lowered
                    for token in forbidden_class_tokens
                )

    runtime_source = inspect.getsource(_runtime_module()).lower()
    for forbidden in (
        "os.kill",
        "killpg",
        "sigterm",
        "sigkill",
        "traceback",
        "exc_info",
        "logger.exception",
        "str(error)",
        "repr(error)",
        "error.args",
    ):
        assert forbidden not in runtime_source


def test_test_double_is_defined_only_in_this_red_file():
    source = Path(__file__).read_text(encoding="utf-8")
    project_root = Path(__file__).resolve().parents[1]

    assert "class _FutureStage8ConsumerDouble" in source
    for path in (project_root / "core").rglob("*.py"):
        assert "FutureStage8ConsumerDouble" not in path.read_text(
            encoding="utf-8"
        )
