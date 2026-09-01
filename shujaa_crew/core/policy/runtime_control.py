from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from core.policy.contracts import (
    AuthorizationDecision,
    AuthorizationEffect,
    AuthorizationRequest,
    RuntimeControlAuthorizationEvaluatorProtocol,
)
from core.work.event_store import (
    AppendReceipt,
    AuditStoreProtocol,
)
from core.work.events import AppendResult, AuditRecord


class RuntimeControlAuthorizationError(ValueError):
    """Structured fail-closed outcome from the authorization gate."""

    def __init__(self, message: str, *, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class RuntimeControlAuthorizationGate:
    """Evaluate and record authorization without executing runtime work."""

    evaluator: RuntimeControlAuthorizationEvaluatorProtocol | None
    audit_store: AuditStoreProtocol | None

    _ACTIONS = frozenset(
        {
            "execution.pause",
            "execution.resume",
            "execution.terminate",
        }
    )

    @staticmethod
    def _audit_id(operation_id: str) -> str:
        digest = sha256(operation_id.encode("utf-8")).hexdigest()
        return f"audit-runtime-control-authorization-{digest}"

    @staticmethod
    def _invalid_request() -> RuntimeControlAuthorizationError:
        return RuntimeControlAuthorizationError(
            "Runtime-control authorization request is invalid.",
            reason_code="AUTHORIZATION_REQUEST_INVALID",
        )

    @staticmethod
    def _evaluator_unavailable() -> RuntimeControlAuthorizationError:
        return RuntimeControlAuthorizationError(
            "Runtime-control authorization evaluator is unavailable.",
            reason_code="EVALUATOR_UNAVAILABLE",
        )

    @staticmethod
    def _audit_unavailable() -> RuntimeControlAuthorizationError:
        return RuntimeControlAuthorizationError(
            "Runtime-control authorization evidence is unavailable.",
            reason_code="AUDIT_UNAVAILABLE",
        )

    def authorize(
        self,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision:
        if not isinstance(request, AuthorizationRequest):
            raise self._invalid_request()

        if (
            request.action not in self._ACTIONS
            or request.resource.resource_type != "execution"
        ):
            raise self._invalid_request()

        evaluator = self.evaluator
        if evaluator is None:
            raise self._evaluator_unavailable()

        try:
            decision = evaluator.evaluate(request)
        except Exception:
            raise self._evaluator_unavailable() from None

        if not isinstance(decision, AuthorizationDecision):
            raise self._evaluator_unavailable()

        if decision.effect is AuthorizationEffect.DENY:
            raise RuntimeControlAuthorizationError(
                "Runtime-control request is denied by policy.",
                reason_code="POLICY_DENIED",
            )

        if decision.effect is not AuthorizationEffect.ALLOW:
            raise self._evaluator_unavailable()

        audit_store = self.audit_store
        if audit_store is None:
            raise self._audit_unavailable()

        audit_record = AuditRecord(
            audit_id=self._audit_id(
                request.context.operation_id
            ),
            action=f"authorization.{request.action}",
            actor_type=request.actor.actor_type,
            actor_id=request.actor.actor_id,
            resource_type=request.resource.resource_type,
            resource_id=request.resource.resource_id,
            outcome="allowed",
            reason_code=decision.reason_code,
            request_id=request.context.request_id,
            operation_id=request.context.operation_id,
            policy_version=decision.policy_version,
        )

        try:
            receipt = audit_store.append_replay_stable(
                audit_record
            )
        except Exception:
            raise self._audit_unavailable() from None

        if (
            not isinstance(receipt, AppendReceipt)
            or receipt.result is not AppendResult.APPENDED
        ):
            raise self._audit_unavailable()

        return decision
