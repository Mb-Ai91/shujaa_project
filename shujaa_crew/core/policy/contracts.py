from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


def _required_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


class AuthorizationEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True)
class ActorRef:
    actor_type: str
    actor_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "actor_type",
            _required_text("actor_type", self.actor_type),
        )
        object.__setattr__(
            self,
            "actor_id",
            _required_text("actor_id", self.actor_id),
        )


@dataclass(frozen=True)
class ResourceRef:
    resource_type: str
    resource_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "resource_type",
            _required_text("resource_type", self.resource_type),
        )
        object.__setattr__(
            self,
            "resource_id",
            _required_text("resource_id", self.resource_id),
        )


@dataclass(frozen=True)
class AuthorizationContext:
    request_id: str
    operation_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_id",
            _required_text("request_id", self.request_id),
        )
        object.__setattr__(
            self,
            "operation_id",
            _required_text("operation_id", self.operation_id),
        )


@dataclass(frozen=True)
class AuthorizationRequest:
    actor: ActorRef
    action: str
    resource: ResourceRef
    context: AuthorizationContext

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorRef):
            raise TypeError("actor must be an ActorRef")
        if not isinstance(self.resource, ResourceRef):
            raise TypeError("resource must be a ResourceRef")
        if not isinstance(self.context, AuthorizationContext):
            raise TypeError(
                "context must be an AuthorizationContext"
            )
        object.__setattr__(
            self,
            "action",
            _required_text("action", self.action),
        )


@dataclass(frozen=True)
class AuthorizationDecision:
    effect: AuthorizationEffect
    reason_code: str
    policy_version: str

    def __post_init__(self) -> None:
        try:
            effect = AuthorizationEffect(self.effect)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "effect must be ALLOW or DENY"
            ) from error
        object.__setattr__(self, "effect", effect)
        object.__setattr__(
            self,
            "reason_code",
            _required_text("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "policy_version",
            _required_text("policy_version", self.policy_version),
        )


class CancelAuthorizationEvaluatorProtocol(Protocol):
    def evaluate(
        self,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision:
        ...


class SubmitAuthorizationEvaluatorProtocol(Protocol):
    def evaluate(
        self,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision:
        ...
