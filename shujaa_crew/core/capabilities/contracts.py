from __future__ import annotations

from typing import Iterable, Protocol

from .models import (
    CapabilityDescriptor,
    CapabilityIdentity,
    CapabilityLifecycle,
    CapabilityRegistrationResult,
    DependencyCandidateDisposition,
    DependencyCycle,
    DependencyResolutionCandidates,
    UnresolvedDependency,
)


class CapabilityCatalogProtocol(Protocol):
    def register(self, candidate: object) -> CapabilityRegistrationResult: ...

    def get(
        self,
        asset_id: str,
        version: str,
    ) -> CapabilityDescriptor | None: ...

    def list(self) -> tuple[CapabilityDescriptor, ...]: ...

    def find_by_capability(
        self,
        capability: str,
        *,
        lifecycle_states: Iterable[CapabilityLifecycle],
    ) -> tuple[CapabilityDescriptor, ...]: ...



class CapabilityDependencyGraphProtocol(Protocol):
    def direct_dependencies(
        self,
        asset_id: str,
        version: str,
    ) -> tuple[str, ...] | None: ...

    def direct_dependents(
        self,
        dependency_asset_id: str,
    ) -> tuple[CapabilityIdentity, ...]: ...

    def unresolved_dependencies(
        self,
    ) -> tuple[UnresolvedDependency, ...]: ...

    def dependency_cycles(self) -> tuple[DependencyCycle, ...]: ...

    def potential_transitive_dependents(
        self,
        dependency_asset_id: str,
    ) -> tuple[CapabilityIdentity, ...]: ...

    def dependency_resolution_candidates(
        self,
        asset_id: str,
        version: str,
    ) -> tuple[DependencyResolutionCandidates, ...] | None: ...
