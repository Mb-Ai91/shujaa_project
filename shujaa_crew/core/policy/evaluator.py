from __future__ import annotations

from dataclasses import dataclass

from core.policy.contracts import (
    ActorRef,
    AuthorizationDecision,
    AuthorizationEffect,
    AuthorizationRequest,
)


@dataclass(frozen=True)
class SinglePrincipalCancelEvaluator:
    """Local single-action policy for the authenticated API channel."""

    principal: ActorRef
    policy_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.principal, ActorRef):
            raise TypeError("principal must be an ActorRef")
        if (
            not isinstance(self.policy_version, str)
            or not self.policy_version.strip()
        ):
            raise ValueError(
                "policy_version must be a non-empty string"
            )
        object.__setattr__(
            self,
            "policy_version",
            self.policy_version.strip(),
        )

    def evaluate(
        self,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision:
        if not isinstance(request, AuthorizationRequest):
            raise TypeError(
                "request must be an AuthorizationRequest"
            )

        allowed = (
            request.actor == self.principal
            and request.action == "task.cancel"
            and request.resource.resource_type == "task"
        )
        return AuthorizationDecision(
            effect=(
                AuthorizationEffect.ALLOW
                if allowed
                else AuthorizationEffect.DENY
            ),
            reason_code=(
                "cancel_allowed"
                if allowed
                else "cancel_denied"
            ),
            policy_version=self.policy_version,
        )


@dataclass(frozen=True)
class SinglePrincipalSubmitEvaluator:
    """Local single-action policy for work submission."""

    principal: ActorRef
    policy_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.principal, ActorRef):
            raise TypeError("principal must be an ActorRef")
        if (
            not isinstance(self.policy_version, str)
            or not self.policy_version.strip()
        ):
            raise ValueError(
                "policy_version must be a non-empty string"
            )
        object.__setattr__(
            self,
            "policy_version",
            self.policy_version.strip(),
        )

    def evaluate(
        self,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision:
        if not isinstance(request, AuthorizationRequest):
            raise TypeError(
                "request must be an AuthorizationRequest"
            )

        allowed = (
            request.actor == self.principal
            and request.action == "work.submit"
            and (
                request.resource.resource_type
                == "work_submission"
            )
        )
        return AuthorizationDecision(
            effect=(
                AuthorizationEffect.ALLOW
                if allowed
                else AuthorizationEffect.DENY
            ),
            reason_code=(
                "submit_allowed"
                if allowed
                else "submit_denied"
            ),
            policy_version=self.policy_version,
        )
