from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from inspect import Parameter, signature
from threading import Barrier
from types import SimpleNamespace

import pytest


EXPECTED_ASSET_TYPES = (
    "AGENT",
    "TOOL",
    "SKILL",
    "MODEL",
    "CONNECTOR",
    "RUNTIME",
    "WORKFLOW_ENGINE",
)

EXPECTED_LIFECYCLES = (
    "SANDBOX",
    "STAGING",
    "ACTIVE",
    "DEPRECATED",
    "RETIRED",
    "QUARANTINED",
)

EXPECTED_REGISTRATION_DISPOSITIONS = (
    "REGISTERED",
    "IDEMPOTENT_REPLAY",
    "IDENTITY_CONFLICT",
    "SCHEMA_REJECTED",
)


class _MissingStage61Implementation:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def __getattr__(self, name):
        pytest.fail(
            "Stage 6.1 production implementation is missing: "
            f"{self.error}",
            pytrace=False,
        )


@pytest.fixture
def api():
    try:
        from core.capabilities.catalog import InMemoryCapabilityCatalog
        from core.capabilities.models import (
            CapabilityAssetType,
            CapabilityDescriptor,
            CapabilityLifecycle,
            CapabilityRegistrationDisposition,
            CapabilityRegistrationResult,
        )
    except (ImportError, ModuleNotFoundError) as error:
        return _MissingStage61Implementation(error)

    return SimpleNamespace(
        AssetType=CapabilityAssetType,
        Catalog=InMemoryCapabilityCatalog,
        Descriptor=CapabilityDescriptor,
        Lifecycle=CapabilityLifecycle,
        RegistrationDisposition=(
            CapabilityRegistrationDisposition
        ),
        RegistrationResult=CapabilityRegistrationResult,
    )


def descriptor(api, **overrides):
    values = {
        "asset_id": "research-agent",
        "version": "v1",
        "asset_type": api.AssetType.AGENT,
        "capabilities": ("analysis", "research"),
        "lifecycle": api.Lifecycle.SANDBOX,
        "dependency_asset_ids": (),
        "provenance": "local-test",
        "risk_tier": None,
        "required_permissions": (),
    }
    values.update(overrides)
    return api.Descriptor(**values)


def disposition(result):
    return result.disposition


def test_capability_asset_type_values_are_closed_and_canonical(api):
    assert tuple(item.name for item in api.AssetType) == (
        EXPECTED_ASSET_TYPES
    )
    assert not hasattr(api.AssetType, "OTHER")
    assert not hasattr(api.AssetType, "STORAGE")
    assert not hasattr(api.AssetType, "OBSERVABILITY")
    assert not hasattr(api.AssetType, "EVALUATOR")


def test_capability_lifecycle_values_are_closed_and_canonical(api):
    assert tuple(item.name for item in api.Lifecycle) == (
        EXPECTED_LIFECYCLES
    )


def test_registration_disposition_values_are_structured(api):
    assert tuple(
        item.name for item in api.RegistrationDisposition
    ) == EXPECTED_REGISTRATION_DISPOSITIONS

    result = api.RegistrationResult(
        disposition=api.RegistrationDisposition.REGISTERED
    )

    assert result.disposition is (
        api.RegistrationDisposition.REGISTERED
    )
    assert not isinstance(result, bool)


def test_asset_id_version_and_provenance_are_required(api):
    parameters = signature(api.Descriptor).parameters

    for field_name in ("asset_id", "version", "provenance"):
        assert parameters[field_name].default is Parameter.empty


def test_descriptor_has_only_the_approved_fields(api):
    assert tuple(item.name for item in fields(api.Descriptor)) == (
        "asset_id",
        "version",
        "asset_type",
        "capabilities",
        "lifecycle",
        "dependency_asset_ids",
        "provenance",
        "risk_tier",
        "required_permissions",
    )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("asset_id", None),
        ("asset_id", 1),
        ("asset_id", ""),
        ("asset_id", "   "),
        ("asset_id", " asset"),
        ("asset_id", "asset "),
        ("version", None),
        ("version", 1),
        ("version", ""),
        ("version", "   "),
        ("version", " v1"),
        ("version", "v1 "),
        ("provenance", None),
        ("provenance", 1),
        ("provenance", ""),
        ("provenance", "   "),
        ("provenance", " local"),
        ("provenance", "local "),
    ],
)
def test_invalid_required_scalar_is_schema_rejected(
    api,
    field_name,
    invalid_value,
):
    catalog = api.Catalog()
    candidate = descriptor(api, **{field_name: invalid_value})

    result = catalog.register(candidate)

    assert disposition(result) is (
        api.RegistrationDisposition.SCHEMA_REJECTED
    )
    assert catalog.list() == ()


def test_none_risk_tier_is_allowed(api):
    catalog = api.Catalog()

    result = catalog.register(descriptor(api, risk_tier=None))

    assert disposition(result) is (
        api.RegistrationDisposition.REGISTERED
    )


@pytest.mark.parametrize(
    "invalid_risk_tier",
    [1, "", "   ", " low", "low "],
)
def test_invalid_non_none_risk_tier_is_schema_rejected(
    api,
    invalid_risk_tier,
):
    catalog = api.Catalog()

    result = catalog.register(
        descriptor(api, risk_tier=invalid_risk_tier)
    )

    assert disposition(result) is (
        api.RegistrationDisposition.SCHEMA_REJECTED
    )
    assert catalog.list() == ()


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("asset_type", "agent"),
        ("asset_type", None),
        ("lifecycle", "active"),
        ("lifecycle", None),
    ],
)
def test_invalid_enum_field_is_schema_rejected(
    api,
    field_name,
    invalid_value,
):
    catalog = api.Catalog()

    result = catalog.register(
        descriptor(api, **{field_name: invalid_value})
    )

    assert disposition(result) is (
        api.RegistrationDisposition.SCHEMA_REJECTED
    )
    assert catalog.list() == ()


@pytest.mark.parametrize(
    ("field_name", "invalid_collection"),
    [
        ("capabilities", ("research", 1)),
        ("capabilities", ("research", "")),
        ("capabilities", ("research", "   ")),
        ("required_permissions", ("read", 1)),
        ("required_permissions", ("read", "")),
        ("dependency_asset_ids", ("asset-b", 1)),
        ("dependency_asset_ids", ("asset-b", "")),
        ("dependency_asset_ids", (" asset-b",)),
        ("dependency_asset_ids", ("asset-b ",)),
    ],
)
def test_invalid_collection_is_schema_rejected(
    api,
    field_name,
    invalid_collection,
):
    catalog = api.Catalog()

    result = catalog.register(
        descriptor(api, **{field_name: invalid_collection})
    )

    assert disposition(result) is (
        api.RegistrationDisposition.SCHEMA_REJECTED
    )
    assert catalog.list() == ()


@pytest.mark.parametrize(
    ("field_name", "duplicate_values"),
    [
        ("capabilities", ("Read", " read ")),
        ("required_permissions", ("WRITE", " write ")),
        ("dependency_asset_ids", ("asset-b", "asset-b")),
    ],
)
def test_semantic_duplicates_are_schema_rejected(
    api,
    field_name,
    duplicate_values,
):
    catalog = api.Catalog()

    result = catalog.register(
        descriptor(api, **{field_name: duplicate_values})
    )

    assert disposition(result) is (
        api.RegistrationDisposition.SCHEMA_REJECTED
    )
    assert catalog.list() == ()


def test_collections_are_stored_as_canonical_deterministic_tuples(api):
    catalog = api.Catalog()
    candidate = descriptor(
        api,
        capabilities=(" Write ", "READ"),
        dependency_asset_ids=("asset-b", "asset-a"),
        required_permissions=(" EXECUTE ", "Read"),
    )

    result = catalog.register(candidate)
    stored = catalog.get("research-agent", "v1")

    assert disposition(result) is (
        api.RegistrationDisposition.REGISTERED
    )
    assert stored is not None
    assert stored.capabilities == ("read", "write")
    assert stored.dependency_asset_ids == (
        "asset-a",
        "asset-b",
    )
    assert stored.required_permissions == (
        "execute",
        "read",
    )
    assert isinstance(stored.capabilities, tuple)
    assert isinstance(stored.dependency_asset_ids, tuple)
    assert isinstance(stored.required_permissions, tuple)


def test_dependency_asset_ids_remain_case_sensitive(api):
    catalog = api.Catalog()
    candidate = descriptor(
        api,
        dependency_asset_ids=("Dependency", "dependency"),
    )

    result = catalog.register(candidate)
    stored = catalog.get("research-agent", "v1")

    assert disposition(result) is (
        api.RegistrationDisposition.REGISTERED
    )
    assert stored is not None
    assert stored.dependency_asset_ids == (
        "Dependency",
        "dependency",
    )


def test_input_order_alone_is_idempotent_replay(api):
    catalog = api.Catalog()
    first = descriptor(
        api,
        capabilities=("read", "write"),
        dependency_asset_ids=("asset-a", "asset-b"),
        required_permissions=("execute", "read"),
    )
    reordered = descriptor(
        api,
        capabilities=("WRITE", "Read"),
        dependency_asset_ids=("asset-b", "asset-a"),
        required_permissions=("READ", "Execute"),
    )

    first_result = catalog.register(first)
    replay_result = catalog.register(reordered)

    assert disposition(first_result) is (
        api.RegistrationDisposition.REGISTERED
    )
    assert disposition(replay_result) is (
        api.RegistrationDisposition.IDEMPOTENT_REPLAY
    )
    assert len(catalog.list()) == 1


@pytest.mark.parametrize(
    ("field_name", "different_value"),
    [
        ("asset_type", "TOOL"),
        ("lifecycle", "ACTIVE"),
        ("capabilities", ("different",)),
        ("dependency_asset_ids", ("different-asset",)),
        ("provenance", "different-source"),
        ("risk_tier", "high"),
        ("required_permissions", ("different",)),
    ],
)
def test_same_identity_with_any_semantic_difference_conflicts(
    api,
    field_name,
    different_value,
):
    catalog = api.Catalog()
    original = descriptor(api)

    if field_name == "asset_type":
        different_value = api.AssetType[different_value]
    elif field_name == "lifecycle":
        different_value = api.Lifecycle[different_value]

    conflicting = descriptor(
        api,
        **{field_name: different_value},
    )

    first_result = catalog.register(original)
    conflict_result = catalog.register(conflicting)

    assert disposition(first_result) is (
        api.RegistrationDisposition.REGISTERED
    )
    assert disposition(conflict_result) is (
        api.RegistrationDisposition.IDENTITY_CONFLICT
    )
    assert catalog.get("research-agent", "v1") == original
    assert len(catalog.list()) == 1


def test_exact_same_descriptor_is_idempotent_replay(api):
    catalog = api.Catalog()
    candidate = descriptor(api)

    first = catalog.register(candidate)
    second = catalog.register(candidate)

    assert disposition(first) is (
        api.RegistrationDisposition.REGISTERED
    )
    assert disposition(second) is (
        api.RegistrationDisposition.IDEMPOTENT_REPLAY
    )


def test_schema_rejected_descriptor_is_not_stored(api):
    catalog = api.Catalog()
    invalid = descriptor(api, provenance=" ")

    result = catalog.register(invalid)

    assert disposition(result) is (
        api.RegistrationDisposition.SCHEMA_REJECTED
    )
    assert catalog.get("research-agent", "v1") is None
    assert catalog.list() == ()


def test_get_uses_exact_asset_id_and_version(api):
    catalog = api.Catalog()
    first = descriptor(api, asset_id="asset-a", version="v1")
    second = descriptor(api, asset_id="asset-a", version="release")
    third = descriptor(api, asset_id="Asset-A", version="v1")

    for candidate in (first, second, third):
        assert disposition(catalog.register(candidate)) is (
            api.RegistrationDisposition.REGISTERED
        )

    assert catalog.get("asset-a", "v1") == first
    assert catalog.get("asset-a", "release") == second
    assert catalog.get("Asset-A", "v1") == third
    assert catalog.get("asset-a", "missing") is None
    assert catalog.get("missing", "v1") is None

    with pytest.raises(TypeError):
        catalog.get("asset-a")


def test_list_is_immutable_deterministic_and_includes_all_versions(api):
    catalog = api.Catalog()
    candidates = (
        descriptor(api, asset_id="asset-b", version="v1"),
        descriptor(api, asset_id="asset-a", version="v2"),
        descriptor(api, asset_id="asset-a", version="v1"),
    )

    for candidate in candidates:
        catalog.register(candidate)

    result = catalog.list()

    assert isinstance(result, tuple)
    assert tuple(
        (item.asset_id, item.version) for item in result
    ) == (
        ("asset-a", "v1"),
        ("asset-a", "v2"),
        ("asset-b", "v1"),
    )


def test_find_requires_explicit_lifecycle_states(api):
    catalog = api.Catalog()

    with pytest.raises(TypeError):
        catalog.find_by_capability("research")


def test_find_with_empty_lifecycle_set_returns_empty_tuple(api):
    catalog = api.Catalog()
    catalog.register(descriptor(api))

    result = catalog.find_by_capability(
        "research",
        lifecycle_states=frozenset(),
    )

    assert result == ()
    assert isinstance(result, tuple)


def test_find_uses_exact_canonical_capability_without_fuzzy_match(api):
    catalog = api.Catalog()
    catalog.register(
        descriptor(api, capabilities=("Research",))
    )

    exact = catalog.find_by_capability(
        " RESEARCH ",
        lifecycle_states=frozenset({api.Lifecycle.SANDBOX}),
    )
    fuzzy = catalog.find_by_capability(
        "search",
        lifecycle_states=frozenset({api.Lifecycle.SANDBOX}),
    )

    assert len(exact) == 1
    assert fuzzy == ()


def test_find_does_not_assume_active_lifecycle(api):
    catalog = api.Catalog()
    sandbox = descriptor(
        api,
        asset_id="sandbox-asset",
        lifecycle=api.Lifecycle.SANDBOX,
    )
    active = descriptor(
        api,
        asset_id="active-asset",
        lifecycle=api.Lifecycle.ACTIVE,
    )

    catalog.register(sandbox)
    catalog.register(active)

    sandbox_only = catalog.find_by_capability(
        "research",
        lifecycle_states=frozenset({api.Lifecycle.SANDBOX}),
    )

    assert sandbox_only == (sandbox,)


def test_find_returns_all_versions_in_deterministic_order(api):
    catalog = api.Catalog()
    candidates = (
        descriptor(api, asset_id="asset-b", version="v1"),
        descriptor(api, asset_id="asset-a", version="v2"),
        descriptor(api, asset_id="asset-a", version="v1"),
    )

    for candidate in candidates:
        catalog.register(candidate)

    result = catalog.find_by_capability(
        "analysis",
        lifecycle_states=frozenset({api.Lifecycle.SANDBOX}),
    )

    assert isinstance(result, tuple)
    assert tuple(
        (item.asset_id, item.version) for item in result
    ) == (
        ("asset-a", "v1"),
        ("asset-a", "v2"),
        ("asset-b", "v1"),
    )


def test_find_does_not_enforce_declared_permissions(api):
    catalog = api.Catalog()
    candidate = descriptor(
        api,
        required_permissions=("admin-only",),
    )
    catalog.register(candidate)

    result = catalog.find_by_capability(
        "research",
        lifecycle_states=frozenset({api.Lifecycle.SANDBOX}),
    )

    assert len(result) == 1


def test_descriptor_and_collection_fields_are_immutable(api):
    catalog = api.Catalog()
    catalog.register(descriptor(api))
    stored = catalog.get("research-agent", "v1")

    assert stored is not None
    assert isinstance(stored.capabilities, tuple)
    assert isinstance(stored.dependency_asset_ids, tuple)
    assert isinstance(stored.required_permissions, tuple)

    with pytest.raises(AttributeError):
        stored.version = "changed"


def test_list_returns_snapshot_not_mutable_catalog_state(api):
    catalog = api.Catalog()
    first = descriptor(api, asset_id="asset-a")
    second = descriptor(api, asset_id="asset-b")
    catalog.register(first)

    snapshot = catalog.list()
    catalog.register(second)

    assert snapshot == (first,)
    assert catalog.list() == (first, second)
    with pytest.raises(AttributeError):
        snapshot.append(second)


def test_find_returns_snapshot_not_mutable_catalog_state(api):
    catalog = api.Catalog()
    first = descriptor(api, asset_id="asset-a")
    second = descriptor(api, asset_id="asset-b")
    catalog.register(first)

    snapshot = catalog.find_by_capability(
        "research",
        lifecycle_states=frozenset({api.Lifecycle.SANDBOX}),
    )
    catalog.register(second)

    assert snapshot == (first,)
    assert len(
        catalog.find_by_capability(
            "research",
            lifecycle_states=frozenset(
                {api.Lifecycle.SANDBOX}
            ),
        )
    ) == 2
    with pytest.raises(AttributeError):
        snapshot.append(second)


def test_missing_declared_dependency_does_not_block_registration(api):
    catalog = api.Catalog()
    candidate = descriptor(
        api,
        dependency_asset_ids=("missing-dependency",),
    )

    result = catalog.register(candidate)

    assert disposition(result) is (
        api.RegistrationDisposition.REGISTERED
    )
    assert catalog.get("missing-dependency", "v1") is None
    assert catalog.list() == (candidate,)


def test_dependency_declarations_allow_cycles_without_traversal(api):
    catalog = api.Catalog()
    first = descriptor(
        api,
        asset_id="asset-a",
        dependency_asset_ids=("asset-b",),
    )
    second = descriptor(
        api,
        asset_id="asset-b",
        dependency_asset_ids=("asset-a",),
    )

    assert disposition(catalog.register(first)) is (
        api.RegistrationDisposition.REGISTERED
    )
    assert disposition(catalog.register(second)) is (
        api.RegistrationDisposition.REGISTERED
    )
    assert catalog.list() == (first, second)


def test_dependency_declaration_does_not_resolve_a_version(api):
    catalog = api.Catalog()
    dependency_v1 = descriptor(
        api,
        asset_id="dependency",
        version="v1",
    )
    dependency_v2 = descriptor(
        api,
        asset_id="dependency",
        version="release-two",
    )
    dependent = descriptor(
        api,
        asset_id="dependent",
        dependency_asset_ids=("dependency",),
    )

    for candidate in (dependency_v1, dependency_v2, dependent):
        assert disposition(catalog.register(candidate)) is (
            api.RegistrationDisposition.REGISTERED
        )

    stored = catalog.get("dependent", "v1")
    assert stored is not None
    assert stored.dependency_asset_ids == ("dependency",)
    assert len(catalog.list()) == 3


def test_concurrent_identical_registration_is_atomic(api):
    catalog = api.Catalog()
    candidate = descriptor(api)
    workers = 16
    barrier = Barrier(workers)

    def register_identical():
        barrier.wait()
        return disposition(catalog.register(candidate))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = tuple(
            executor.map(
                lambda _index: register_identical(),
                range(workers),
            )
        )

    assert results.count(
        api.RegistrationDisposition.REGISTERED
    ) == 1
    assert results.count(
        api.RegistrationDisposition.IDEMPOTENT_REPLAY
    ) == workers - 1
    assert catalog.list() == (candidate,)


def test_concurrent_conflicting_registration_is_atomic(api):
    catalog = api.Catalog()
    first = descriptor(api, provenance="source-a")
    second = descriptor(api, provenance="source-b")
    barrier = Barrier(2)

    def register_candidate(candidate):
        barrier.wait()
        return candidate, disposition(catalog.register(candidate))

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(
            executor.map(register_candidate, (first, second))
        )

    dispositions = tuple(item[1] for item in results)
    assert dispositions.count(
        api.RegistrationDisposition.REGISTERED
    ) == 1
    assert dispositions.count(
        api.RegistrationDisposition.IDENTITY_CONFLICT
    ) == 1

    winner = next(
        candidate
        for candidate, item_disposition in results
        if item_disposition
        is api.RegistrationDisposition.REGISTERED
    )
    assert catalog.get("research-agent", "v1") == winner
    assert len(catalog.list()) == 1


def test_multiple_concurrent_conflicting_contenders_leave_one_record(api):
    catalog = api.Catalog()
    workers = 12
    barrier = Barrier(workers)
    candidates = tuple(
        descriptor(api, provenance=f"source-{index}")
        for index in range(workers)
    )

    def register_candidate(candidate):
        barrier.wait()
        return candidate, disposition(catalog.register(candidate))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = tuple(executor.map(register_candidate, candidates))

    dispositions = tuple(item[1] for item in results)
    assert dispositions.count(
        api.RegistrationDisposition.REGISTERED
    ) == 1
    assert dispositions.count(
        api.RegistrationDisposition.IDENTITY_CONFLICT
    ) == workers - 1

    winner = next(
        candidate
        for candidate, item_disposition in results
        if item_disposition
        is api.RegistrationDisposition.REGISTERED
    )
    assert catalog.get("research-agent", "v1") == winner
    assert catalog.list() == (winner,)
