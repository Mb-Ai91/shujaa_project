from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityAssetType(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    SKILL = "skill"
    MODEL = "model"
    CONNECTOR = "connector"
    RUNTIME = "runtime"
    WORKFLOW_ENGINE = "workflow_engine"


class CapabilityLifecycle(str, Enum):
    SANDBOX = "sandbox"
    STAGING = "staging"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class CapabilityDescriptor:
    asset_id: str
    version: str
    asset_type: CapabilityAssetType
    capabilities: tuple[str, ...]
    lifecycle: CapabilityLifecycle
    dependency_asset_ids: tuple[str, ...]
    provenance: str
    risk_tier: str | None
    required_permissions: tuple[str, ...]


class CapabilityRegistrationDisposition(str, Enum):
    REGISTERED = "registered"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    IDENTITY_CONFLICT = "identity_conflict"
    SCHEMA_REJECTED = "schema_rejected"


@dataclass(frozen=True)
class CapabilityRegistrationResult:
    disposition: CapabilityRegistrationDisposition
