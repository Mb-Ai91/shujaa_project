from __future__ import annotations

from threading import Lock

from .contracts import CapabilityDependencyGraphProtocol
from .models import (
    DependencyBindingProposal,
    DependencyBindingRegistrationDisposition,
    DependencyBindingRegistrationResult,
    ExplicitDependencyBinding,
    ExplicitDependencyBindingSet,
)


def _validated_identity_part(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be non-empty and trimmed")
    return value


class InMemoryExplicitDependencyBindingRegistry:
    def __init__(self, graph: CapabilityDependencyGraphProtocol) -> None:
        self._graph = graph
        self._records: dict[tuple[str, str], ExplicitDependencyBindingSet] = {}
        self._lock = Lock()

    def register(
        self,
        asset_id: str,
        version: str,
        bindings: tuple[DependencyBindingProposal, ...],
    ) -> DependencyBindingRegistrationResult:
        validation = self._graph.validate_dependency_binding_plan(
            asset_id, version, bindings
        )
        if validation is None:
            return DependencyBindingRegistrationResult(
                DependencyBindingRegistrationDisposition.SOURCE_NOT_FOUND,
                None,
            )
        if not validation.structurally_complete:
            return DependencyBindingRegistrationResult(
                DependencyBindingRegistrationDisposition.PLAN_REJECTED,
                validation,
            )

        candidate = ExplicitDependencyBindingSet(
            source_identity=validation.source_identity,
            bindings=tuple(
                ExplicitDependencyBinding(
                    item.dependency_asset_id,
                    item.target_identity,
                )
                for item in validation.binding_validations
            ),
        )
        with self._lock:
            current = self._records.get(candidate.source_identity)
            if current is None:
                self._records[candidate.source_identity] = candidate
                disposition = DependencyBindingRegistrationDisposition.REGISTERED
            elif current == candidate:
                disposition = (
                    DependencyBindingRegistrationDisposition.IDEMPOTENT_REPLAY
                )
            else:
                disposition = (
                    DependencyBindingRegistrationDisposition.IDENTITY_CONFLICT
                )
        return DependencyBindingRegistrationResult(disposition, validation)

    def get(
        self, asset_id: str, version: str
    ) -> ExplicitDependencyBindingSet | None:
        identity = (
            _validated_identity_part(asset_id, "asset_id"),
            _validated_identity_part(version, "version"),
        )
        with self._lock:
            return self._records.get(identity)

    def list(self) -> tuple[ExplicitDependencyBindingSet, ...]:
        with self._lock:
            return tuple(self._records[key] for key in sorted(self._records))
