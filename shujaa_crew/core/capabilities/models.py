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



CapabilityIdentity = tuple[str, str]


@dataclass(frozen=True)
class UnresolvedDependency:
    source_asset_id: str
    source_version: str
    dependency_asset_id: str


@dataclass(frozen=True)
class DependencyCycle:
    asset_ids: tuple[str, ...]


class DependencyCandidateDisposition(str, Enum):
    UNRESOLVED = "unresolved"
    UNIQUE = "unique"
    MULTIPLE_CANDIDATES = "multiple_candidates"


@dataclass(frozen=True)
class DependencyResolutionCandidates:
    dependency_asset_id: str
    candidate_identities: tuple[CapabilityIdentity, ...]
    disposition: DependencyCandidateDisposition


class DependencyBindingDisposition(str, Enum):
    STRUCTURALLY_VALID = "structurally_valid"
    DEPENDENCY_NOT_DECLARED = "dependency_not_declared"
    TARGET_NOT_FOUND = "target_not_found"


@dataclass(frozen=True)
class DependencyBindingValidation:
    dependency_asset_id: str
    target_identity: CapabilityIdentity
    disposition: DependencyBindingDisposition
