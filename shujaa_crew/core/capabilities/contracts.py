from __future__ import annotations

from typing import Iterable, Protocol

from .models import (
    CapabilityDescriptor,
    CapabilityLifecycle,
    CapabilityRegistrationResult,
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
