from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from core.work.models import utc_now


_SCHEMA_VERSION = "1"

_SECRET_KEYS = frozenset(
    {
        "accesstoken",
        "apikey",
        "authorization",
        "clientsecret",
        "cookie",
        "password",
        "privatekey",
        "refreshtoken",
        "secret",
        "secretkey",
        "token",
    }
)

_SECRET_SUFFIXES = (
    "apikey",
    "password",
    "privatekey",
    "secret",
    "token",
)


def new_event_id() -> str:
    return f"event-{uuid4()}"


def new_audit_id() -> str:
    return f"audit-{uuid4()}"


def _normalize_key(value: str) -> str:
    return "".join(
        character
        for character in value.casefold()
        if character.isalnum()
    )


def _is_secret_key(value: str) -> bool:
    normalized = _normalize_key(value)
    return (
        normalized in _SECRET_KEYS
        or any(
            normalized.endswith(suffix)
            for suffix in _SECRET_SUFFIXES
        )
    )


def _required_text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{name} must not be blank")

    return normalized


def _optional_text(
    name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _required_text(name, value)


def _utc_timestamp(
    name: str,
    value: datetime,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{name} must be timezone-aware UTC"
        )

    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must use UTC")

    return value


def _freeze_payload(
    value: Any,
    *,
    path: str = "payload",
) -> Any:
    if value is None or isinstance(
        value,
        (bool, int, str),
    ):
        return value

    if isinstance(value, float):
        if not isfinite(value):
            raise TypeError(
                f"{path} payload values must be "
                "JSON-compatible"
            )

        return value

    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"{path} payload keys must be strings"
                )

            if not key.strip():
                raise ValueError(
                    f"{path} payload keys must not be blank"
                )

            if _is_secret_key(key):
                raise ValueError(
                    f"{path} contains a forbidden "
                    "secret-bearing key"
                )

            frozen[key] = _freeze_payload(
                item,
                path=f"{path}.{key}",
            )

        return MappingProxyType(frozen)

    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_payload(
                item,
                path=f"{path}[]",
            )
            for item in value
        )

    raise TypeError(
        f"{path} payload values must be JSON-compatible"
    )


def _validated_payload(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")

    return _freeze_payload(payload)


class AppendResult(StrEnum):
    APPENDED = "appended"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    IDENTITY_CONFLICT = "identity_conflict"
    SCHEMA_REJECTED = "schema_rejected"
    WRITE_FAILED = "write_failed"


@dataclass(frozen=True)
class WorkEvent:
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    source_component: str
    correlation_id: str
    schema_version: str = _SCHEMA_VERSION
    occurred_at: datetime = field(
        default_factory=utc_now
    )
    recorded_at: datetime = field(
        default_factory=utc_now
    )
    causation_id: str | None = None
    operation_id: str | None = None
    work_id: str | None = None
    task_id: str | None = None
    execution_id: str | None = None
    actor_ref: str | None = None
    capability_asset_id: str | None = None
    resolved_adapter_id: str | None = None
    resolved_adapter_version: str | None = None
    payload: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        for name in (
            "event_id",
            "event_type",
            "entity_type",
            "entity_id",
            "source_component",
            "correlation_id",
        ):
            object.__setattr__(
                self,
                name,
                _required_text(
                    name,
                    getattr(self, name),
                ),
            )

        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "schema_version must be '1'"
            )

        object.__setattr__(
            self,
            "occurred_at",
            _utc_timestamp(
                "occurred_at",
                self.occurred_at,
            ),
        )

        object.__setattr__(
            self,
            "recorded_at",
            _utc_timestamp(
                "recorded_at",
                self.recorded_at,
            ),
        )

        if self.recorded_at < self.occurred_at:
            raise ValueError(
                "recorded_at must not precede occurred_at"
            )

        for name in (
            "causation_id",
            "operation_id",
            "work_id",
            "task_id",
            "execution_id",
            "actor_ref",
            "capability_asset_id",
            "resolved_adapter_id",
            "resolved_adapter_version",
        ):
            object.__setattr__(
                self,
                name,
                _optional_text(
                    name,
                    getattr(self, name),
                ),
            )

        object.__setattr__(
            self,
            "payload",
            _validated_payload(self.payload),
        )

    @property
    def created_at(self) -> datetime:
        return self.occurred_at

    @property
    def actor_id(self) -> str | None:
        return self.actor_ref


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    action: str
    actor_type: str
    actor_id: str
    resource_type: str
    resource_id: str
    outcome: str
    reason_code: str
    schema_version: str = _SCHEMA_VERSION
    recorded_at: datetime = field(
        default_factory=utc_now
    )
    on_behalf_of: str | None = None
    request_id: str | None = None
    operation_id: str | None = None
    event_id: str | None = None
    error_code: str | None = None
    policy_version: str | None = None
    approval_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "audit_id",
            "action",
            "actor_type",
            "actor_id",
            "resource_type",
            "resource_id",
            "outcome",
            "reason_code",
        ):
            object.__setattr__(
                self,
                name,
                _required_text(
                    name,
                    getattr(self, name),
                ),
            )

        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "schema_version must be '1'"
            )

        object.__setattr__(
            self,
            "recorded_at",
            _utc_timestamp(
                "recorded_at",
                self.recorded_at,
            ),
        )

        for name in (
            "on_behalf_of",
            "request_id",
            "operation_id",
            "event_id",
            "error_code",
            "policy_version",
            "approval_id",
        ):
            object.__setattr__(
                self,
                name,
                _optional_text(
                    name,
                    getattr(self, name),
                ),
            )
