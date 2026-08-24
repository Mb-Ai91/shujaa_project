from __future__ import annotations

from threading import RLock
from typing import Iterable

from .models import (
    CapabilityAssetType,
    CapabilityDescriptor,
    CapabilityLifecycle,
    CapabilityRegistrationDisposition,
    CapabilityRegistrationResult,
)


class _SchemaRejected(ValueError):
    pass


def _strict_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise _SchemaRejected(f"{field_name} must be a string")
    if not value or not value.strip() or value != value.strip():
        raise _SchemaRejected(f"{field_name} must be a clean non-empty string")
    return value


def _canonical_casefolded_collection(
    value: object,
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise _SchemaRejected(f"{field_name} must be a tuple")

    canonical: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise _SchemaRejected(f"{field_name} items must be strings")
        normalized = item.strip().casefold()
        if not normalized:
            raise _SchemaRejected(f"{field_name} items must be non-empty")
        canonical.append(normalized)

    if len(canonical) != len(set(canonical)):
        raise _SchemaRejected(f"{field_name} contains semantic duplicates")
    return tuple(sorted(canonical))


def _canonical_dependency_ids(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise _SchemaRejected("dependency_asset_ids must be a tuple")

    dependencies: list[str] = []
    for item in value:
        dependencies.append(_strict_string(item, "dependency_asset_ids item"))

    if len(dependencies) != len(set(dependencies)):
        raise _SchemaRejected("dependency_asset_ids contains duplicates")
    return tuple(sorted(dependencies))


def _canonical_descriptor(candidate: object) -> CapabilityDescriptor:
    if not isinstance(candidate, CapabilityDescriptor):
        raise _SchemaRejected("candidate must be a CapabilityDescriptor")
    if not isinstance(candidate.asset_type, CapabilityAssetType):
        raise _SchemaRejected("asset_type is invalid")
    if not isinstance(candidate.lifecycle, CapabilityLifecycle):
        raise _SchemaRejected("lifecycle is invalid")

    risk_tier = candidate.risk_tier
    if risk_tier is not None:
        risk_tier = _strict_string(risk_tier, "risk_tier")

    return CapabilityDescriptor(
        asset_id=_strict_string(candidate.asset_id, "asset_id"),
        version=_strict_string(candidate.version, "version"),
        asset_type=candidate.asset_type,
        capabilities=_canonical_casefolded_collection(
            candidate.capabilities,
            "capabilities",
        ),
        lifecycle=candidate.lifecycle,
        dependency_asset_ids=_canonical_dependency_ids(
            candidate.dependency_asset_ids
        ),
        provenance=_strict_string(candidate.provenance, "provenance"),
        risk_tier=risk_tier,
        required_permissions=_canonical_casefolded_collection(
            candidate.required_permissions,
            "required_permissions",
        ),
    )


class InMemoryCapabilityCatalog:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], CapabilityDescriptor] = {}
        self._lock = RLock()

    def register(self, candidate: object) -> CapabilityRegistrationResult:
        try:
            canonical = _canonical_descriptor(candidate)
        except _SchemaRejected:
            return CapabilityRegistrationResult(
                CapabilityRegistrationDisposition.SCHEMA_REJECTED
            )

        identity = (canonical.asset_id, canonical.version)
        with self._lock:
            current = self._records.get(identity)
            if current is None:
                self._records[identity] = canonical
                disposition = CapabilityRegistrationDisposition.REGISTERED
            elif current == canonical:
                disposition = (
                    CapabilityRegistrationDisposition.IDEMPOTENT_REPLAY
                )
            else:
                disposition = CapabilityRegistrationDisposition.IDENTITY_CONFLICT

        return CapabilityRegistrationResult(disposition)

    def get(
        self,
        asset_id: str,
        version: str,
    ) -> CapabilityDescriptor | None:
        with self._lock:
            return self._records.get((asset_id, version))

    def list(self) -> tuple[CapabilityDescriptor, ...]:
        with self._lock:
            return tuple(
                self._records[identity]
                for identity in sorted(self._records)
            )

    def find_by_capability(
        self,
        capability: str,
        *,
        lifecycle_states: Iterable[CapabilityLifecycle],
    ) -> tuple[CapabilityDescriptor, ...]:
        if not isinstance(capability, str):
            raise TypeError("capability must be a string")
        canonical_capability = capability.strip().casefold()
        if not canonical_capability:
            return ()

        states = frozenset(lifecycle_states)
        if not states:
            return ()
        if any(not isinstance(state, CapabilityLifecycle) for state in states):
            raise TypeError("lifecycle_states contains an invalid state")

        with self._lock:
            return tuple(
                descriptor
                for identity, descriptor in sorted(self._records.items())
                if descriptor.lifecycle in states
                and canonical_capability in descriptor.capabilities
            )
