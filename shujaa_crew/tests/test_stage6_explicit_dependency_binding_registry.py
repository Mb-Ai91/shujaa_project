from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, fields
from inspect import Parameter, signature
from threading import Barrier
from types import SimpleNamespace
from typing import get_type_hints

import pytest


def _required_api():
    import core.capabilities as capabilities
    from core.capabilities import contracts, models

    return capabilities, contracts, models, {
        "Binding": getattr(models, "ExplicitDependencyBinding", None),
        "BindingSet": getattr(models, "ExplicitDependencyBindingSet", None),
        "Disposition": getattr(
            models,
            "DependencyBindingRegistrationDisposition",
            None,
        ),
        "RegistrationResult": getattr(
            models,
            "DependencyBindingRegistrationResult",
            None,
        ),
        "Protocol": getattr(
            contracts,
            "ExplicitDependencyBindingRegistryProtocol",
            None,
        ),
        "Registry": getattr(
            capabilities,
            "InMemoryExplicitDependencyBindingRegistry",
            None,
        ),
    }


def test_slice_67_public_boundary_exists():
    _, _, _, required = _required_api()
    missing = tuple(name for name, value in required.items() if value is None)
    assert not missing, f"Slice 6.7 public boundary is missing: {missing}"


@pytest.fixture
def api():
    capabilities, _, models, required = _required_api()
    missing = tuple(name for name, value in required.items() if value is None)
    if missing:
        pytest.skip(f"blocked by missing Slice 6.7 boundary: {missing}")

    return SimpleNamespace(
        **required,
        AssetType=models.CapabilityAssetType,
        Descriptor=models.CapabilityDescriptor,
        Graph=capabilities.InMemoryCapabilityDependencyGraph,
        Lifecycle=models.CapabilityLifecycle,
        PlanValidation=models.DependencyBindingPlanValidation,
        Proposal=models.DependencyBindingProposal,
        capabilities=capabilities,
    )


def descriptor(api, asset_id, *, version="v1", dependencies=()):
    return api.Descriptor(
        asset_id=asset_id,
        version=version,
        asset_type=api.AssetType.AGENT,
        capabilities=("binding-registry-test",),
        lifecycle=api.Lifecycle.ACTIVE,
        dependency_asset_ids=dependencies,
        provenance="local-test",
        risk_tier=None,
        required_permissions=(),
    )


def proposal(api, dependency_asset_id, target_version="v1"):
    return api.Proposal(
        dependency_asset_id=dependency_asset_id,
        target_version=target_version,
    )


def registry_for(api, *, source_dependencies=("dep-a", "dep-b")):
    descriptors = [
        descriptor(api, "source", dependencies=source_dependencies),
        descriptor(api, "dep-a", version="v1"),
        descriptor(api, "dep-a", version="v2"),
        descriptor(api, "dep-b", version="v1"),
        descriptor(api, "dep-b", version="v2"),
    ]
    return api.Registry(api.Graph(tuple(descriptors)))


def complete_plan(api, *, a="v1", b="v1", reverse=False):
    bindings = (proposal(api, "dep-a", a), proposal(api, "dep-b", b))
    return tuple(reversed(bindings)) if reverse else bindings


def test_public_models_are_closed_immutable_and_minimal(api):
    assert tuple(item.value for item in api.Disposition) == (
        "registered",
        "idempotent_replay",
        "identity_conflict",
        "source_not_found",
        "plan_rejected",
    )
    assert tuple(field.name for field in fields(api.Binding)) == (
        "dependency_asset_id",
        "target_identity",
    )
    assert tuple(field.name for field in fields(api.BindingSet)) == (
        "source_identity",
        "bindings",
    )
    assert tuple(field.name for field in fields(api.RegistrationResult)) == (
        "disposition",
        "validation",
    )

    item = api.Binding("dep-a", ("dep-a", "v1"))
    with pytest.raises(FrozenInstanceError):
        item.dependency_asset_id = "changed"


def test_public_exports_and_protocol_expose_the_approved_boundary(api):
    assert api.capabilities.ExplicitDependencyBinding is api.Binding
    assert api.capabilities.ExplicitDependencyBindingSet is api.BindingSet
    assert (
        api.capabilities.DependencyBindingRegistrationDisposition
        is api.Disposition
    )
    assert api.capabilities.DependencyBindingRegistrationResult is api.RegistrationResult
    assert api.capabilities.ExplicitDependencyBindingRegistryProtocol is api.Protocol

    assert tuple(signature(api.Protocol.register).parameters) == (
        "self",
        "asset_id",
        "version",
        "bindings",
    )
    assert tuple(signature(api.Protocol.get).parameters) == (
        "self",
        "asset_id",
        "version",
    )
    assert tuple(signature(api.Protocol.list).parameters) == ("self",)
    for parameter in signature(api.Protocol.register).parameters.values():
        if parameter.name != "self":
            assert parameter.default is Parameter.empty


def test_public_protocol_declares_exact_read_return_types(api):
    assert get_type_hints(api.Protocol.get)["return"] == api.BindingSet | None
    assert get_type_hints(api.Protocol.list)["return"] == tuple[api.BindingSet, ...]


@pytest.mark.parametrize(
    ("asset_id", "version", "bindings", "error"),
    (
        (None, "v1", (), TypeError),
        ("source", None, (), TypeError),
        ("", "v1", (), ValueError),
        ("source", " v1", (), ValueError),
        ("source", "v1", None, TypeError),
        ("source", "v1", [], TypeError),
        ("source", "v1", (object(),), TypeError),
    ),
)
def test_register_preserves_plan_validation_input_contract(
    api, asset_id, version, bindings, error
):
    registry = registry_for(api)
    with pytest.raises(error):
        registry.register(asset_id, version, bindings)
    assert registry.list() == ()


def test_missing_source_returns_source_not_found_without_a_write(api):
    registry = registry_for(api)
    result = registry.register("missing", "v1", ())

    assert result.disposition is api.Disposition.SOURCE_NOT_FOUND
    assert result.validation is None
    assert registry.get("missing", "v1") is None
    assert registry.list() == ()


def test_incomplete_or_invalid_plan_is_rejected_without_partial_write(api):
    registry = registry_for(api)
    attempts = (
        (proposal(api, "dep-a"),),
        complete_plan(api) + (proposal(api, "undeclared"),),
    )

    for bindings in attempts:
        result = registry.register("source", "v1", bindings)
        assert result.disposition is api.Disposition.PLAN_REJECTED
        assert result.validation is not None
        assert result.validation.structurally_complete is False
        assert registry.get("source", "v1") is None
    assert registry.list() == ()


def test_rejected_plan_preserves_existing_winner_and_reports_current_attempt(api):
    registry = registry_for(api)
    registered = registry.register("source", "v1", complete_plan(api))
    winner = registry.get("source", "v1")
    listed_before = registry.list()

    rejected = registry.register(
        "source",
        "v1",
        (proposal(api, "dep-a", "v2"),),
    )

    assert registered.disposition is api.Disposition.REGISTERED
    assert rejected.disposition is api.Disposition.PLAN_REJECTED
    assert rejected.validation is not None
    assert rejected.validation.structurally_complete is False
    assert rejected.validation.binding_validations[0].target_identity == (
        "dep-a",
        "v2",
    )
    assert registry.get("source", "v1") == winner
    assert registry.list() == listed_before


def test_registration_uses_canonical_validation_order_and_is_immutable(api):
    registry = registry_for(api)
    result = registry.register(
        "source",
        "v1",
        complete_plan(api, a="v2", reverse=True),
    )

    assert result.disposition is api.Disposition.REGISTERED
    assert result.validation is not None
    stored = registry.get("source", "v1")
    assert stored == api.BindingSet(
        source_identity=("source", "v1"),
        bindings=(
            api.Binding("dep-a", ("dep-a", "v2")),
            api.Binding("dep-b", ("dep-b", "v1")),
        ),
    )
    assert isinstance(stored.bindings, tuple)
    with pytest.raises(FrozenInstanceError):
        stored.source_identity = ("changed", "v1")


def test_reordered_equivalent_plan_is_idempotent_replay(api):
    registry = registry_for(api)
    first = registry.register("source", "v1", complete_plan(api))
    replay = registry.register(
        "source", "v1", complete_plan(api, reverse=True)
    )

    assert first.disposition is api.Disposition.REGISTERED
    assert replay.disposition is api.Disposition.IDEMPOTENT_REPLAY
    assert replay.validation is not None
    assert registry.list() == (registry.get("source", "v1"),)


def test_conflict_reports_current_attempt_validation_and_preserves_winner(api):
    registry = registry_for(api)
    registry.register("source", "v1", complete_plan(api, a="v1"))
    winner = registry.get("source", "v1")

    conflict = registry.register("source", "v1", complete_plan(api, a="v2"))

    assert conflict.disposition is api.Disposition.IDENTITY_CONFLICT
    assert conflict.validation is not None
    assert conflict.validation.binding_validations[0].target_identity == (
        "dep-a",
        "v2",
    )
    assert registry.get("source", "v1") == winner


def test_get_validates_identity_and_list_is_deterministically_sorted(api):
    graph = api.Graph(
        (
            descriptor(api, "z-source", dependencies=("dep-a",)),
            descriptor(api, "a-source", version="v2", dependencies=("dep-a",)),
            descriptor(api, "dep-a"),
        )
    )
    registry = api.Registry(graph)
    one = (proposal(api, "dep-a"),)
    registry.register("z-source", "v1", one)
    registry.register("a-source", "v2", one)

    assert tuple(item.source_identity for item in registry.list()) == (
        ("a-source", "v2"),
        ("z-source", "v1"),
    )
    assert registry.get("not-registered", "v1") is None
    with pytest.raises(TypeError):
        registry.get(None, "v1")
    with pytest.raises(ValueError):
        registry.get("bad ", "v1")


class CountingGraph:
    def __init__(self, graph):
        self.graph = graph
        self.calls = 0

    def validate_dependency_binding_plan(self, asset_id, version, bindings):
        self.calls += 1
        return self.graph.validate_dependency_binding_plan(
            asset_id, version, bindings
        )


def test_each_attempt_validates_exactly_once(api):
    graph = CountingGraph(
        api.Graph(
            (
                descriptor(api, "source", dependencies=("dep-a",)),
                descriptor(api, "dep-a"),
            )
        )
    )
    registry = api.Registry(graph)
    bindings = (proposal(api, "dep-a"),)

    registry.register("source", "v1", bindings)
    registry.register("source", "v1", bindings)
    assert graph.calls == 2


def test_concurrent_identical_attempts_have_one_registration(api):
    registry = registry_for(api)
    workers = 8
    barrier = Barrier(workers)

    def register():
        barrier.wait()
        return registry.register("source", "v1", complete_plan(api))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = tuple(executor.map(lambda _: register(), range(workers)))

    dispositions = tuple(result.disposition for result in results)
    assert dispositions.count(api.Disposition.REGISTERED) == 1
    assert dispositions.count(api.Disposition.IDEMPOTENT_REPLAY) == workers - 1
    assert len(registry.list()) == 1


def test_concurrent_conflicting_attempts_preserve_one_scheduling_winner(api):
    registry = registry_for(api)
    barrier = Barrier(2)
    plans = (complete_plan(api, a="v1"), complete_plan(api, a="v2"))

    def register(bindings):
        barrier.wait()
        return registry.register("source", "v1", bindings)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(register, plans))

    dispositions = {result.disposition for result in results}
    assert dispositions == {
        api.Disposition.REGISTERED,
        api.Disposition.IDENTITY_CONFLICT,
    }
    stored = registry.get("source", "v1")
    assert stored.bindings[0].target_identity in {
        ("dep-a", "v1"),
        ("dep-a", "v2"),
    }
    assert len(registry.list()) == 1
