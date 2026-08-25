from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from inspect import Parameter, signature
from types import SimpleNamespace

import pytest


class _MissingStage62Implementation:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def __getattr__(self, name):
        pytest.fail(
            "Stage 6.2 production implementation is missing: "
            f"{self.error}",
            pytrace=False,
        )


@pytest.fixture
def api():
    try:
        from core.capabilities import (
            CapabilityDependencyGraphProtocol,
            DependencyCycle,
            InMemoryCapabilityDependencyGraph,
            UnresolvedDependency,
        )
        from core.capabilities.catalog import InMemoryCapabilityCatalog
        from core.capabilities.models import (
            CapabilityAssetType,
            CapabilityDescriptor,
            CapabilityLifecycle,
        )
    except (ImportError, ModuleNotFoundError) as error:
        return _MissingStage62Implementation(error)

    return SimpleNamespace(
        AssetType=CapabilityAssetType,
        Catalog=InMemoryCapabilityCatalog,
        Cycle=DependencyCycle,
        Descriptor=CapabilityDescriptor,
        Graph=InMemoryCapabilityDependencyGraph,
        Lifecycle=CapabilityLifecycle,
        Protocol=CapabilityDependencyGraphProtocol,
        Unresolved=UnresolvedDependency,
    )


def descriptor(api, asset_id, version="v1", dependencies=(), **overrides):
    values = {
        "asset_id": asset_id,
        "version": version,
        "asset_type": api.AssetType.AGENT,
        "capabilities": ("analysis",),
        "lifecycle": api.Lifecycle.SANDBOX,
        "dependency_asset_ids": dependencies,
        "provenance": "local-test",
        "risk_tier": None,
        "required_permissions": (),
    }
    values.update(overrides)
    return api.Descriptor(**values)


def graph(api, *descriptors):
    return api.Graph(tuple(descriptors))


def test_public_models_have_only_the_approved_fields(api):
    assert tuple(item.name for item in fields(api.Unresolved)) == (
        "source_asset_id",
        "source_version",
        "dependency_asset_id",
    )
    assert tuple(item.name for item in fields(api.Cycle)) == ("asset_ids",)


def test_protocol_exposes_only_the_approved_queries():
    from core.capabilities.contracts import (
        CapabilityDependencyGraphProtocol,
    )

    public_queries = {
        name
        for name, value in vars(
            CapabilityDependencyGraphProtocol
        ).items()
        if not name.startswith("_") and callable(value)
    }

    assert public_queries == {
        "direct_dependencies",
        "direct_dependents",
        "unresolved_dependencies",
        "dependency_cycles",
        "potential_transitive_dependents",
    }


def test_direct_dependency_signature_distinguishes_missing_source(api):
    parameters = signature(api.Protocol.direct_dependencies).parameters
    assert tuple(parameters) == ("self", "asset_id", "version")
    assert all(
        parameters[name].default is Parameter.empty
        for name in ("asset_id", "version")
    )


def test_empty_snapshot_is_valid_and_empty(api):
    subject = graph(api)
    assert subject.direct_dependencies("missing", "v1") is None
    assert subject.direct_dependents("missing") == ()
    assert subject.unresolved_dependencies() == ()
    assert subject.dependency_cycles() == ()


def test_constructor_accepts_a_tuple_snapshot_not_a_live_catalog(api):
    catalog = api.Catalog()
    with pytest.raises(TypeError):
        api.Graph(catalog)


def test_missing_source_differs_from_source_without_dependencies(api):
    subject = graph(api, descriptor(api, "source"))
    assert subject.direct_dependencies("missing", "v1") is None
    assert subject.direct_dependencies("source", "v1") == ()


def test_direct_dependencies_are_deduplicated_and_deterministic(api):
    subject = graph(
        api,
        descriptor(api, "source", dependencies=("zeta", "alpha")),
        descriptor(api, "alpha"),
        descriptor(api, "zeta"),
    )
    assert subject.direct_dependencies("source", "v1") == (
        "alpha",
        "zeta",
    )


def test_direct_dependents_return_exact_source_identities_for_all_versions(api):
    subject = graph(
        api,
        descriptor(api, "source-b", "v2", ("target",)),
        descriptor(api, "source-a", "v2", ("target",)),
        descriptor(api, "source-a", "v1", ("target",)),
        descriptor(api, "target", "v9"),
    )
    assert subject.direct_dependents("target") == (
        ("source-a", "v1"),
        ("source-a", "v2"),
        ("source-b", "v2"),
    )


def test_direct_dependents_do_not_require_the_target_to_be_registered(api):
    subject = graph(
        api,
        descriptor(api, "source", dependencies=("absent",)),
    )
    assert subject.direct_dependents("absent") == (("source", "v1"),)


def test_any_registered_version_resolves_dependency_without_latest_binding(api):
    subject = graph(
        api,
        descriptor(api, "source", dependencies=("target",)),
        descriptor(api, "target", "old"),
        descriptor(api, "target", "new"),
    )
    assert subject.unresolved_dependencies() == ()


def test_resolution_ignores_lifecycle(api):
    subject = graph(
        api,
        descriptor(api, "source", dependencies=("target",)),
        descriptor(
            api,
            "target",
            lifecycle=api.Lifecycle.RETIRED,
        ),
    )
    assert subject.unresolved_dependencies() == ()


def test_unresolved_results_preserve_exact_source_identity_and_order(api):
    subject = graph(
        api,
        descriptor(api, "source-b", "v2", ("missing-z",)),
        descriptor(
            api,
            "source-a",
            "v2",
            ("missing-z", "missing-a"),
        ),
        descriptor(api, "source-a", "v1", ("missing-z",)),
    )
    assert subject.unresolved_dependencies() == (
        api.Unresolved("source-a", "v1", "missing-z"),
        api.Unresolved("source-a", "v2", "missing-a"),
        api.Unresolved("source-a", "v2", "missing-z"),
        api.Unresolved("source-b", "v2", "missing-z"),
    )


def test_acyclic_edges_do_not_create_cycles(api):
    subject = graph(
        api,
        descriptor(api, "a", dependencies=("b",)),
        descriptor(api, "b", dependencies=("c",)),
        descriptor(api, "c"),
    )
    assert subject.dependency_cycles() == ()


def test_multi_node_scc_is_one_deterministic_cycle_record(api):
    subject = graph(
        api,
        descriptor(api, "c", dependencies=("a",)),
        descriptor(api, "a", dependencies=("b",)),
        descriptor(api, "b", dependencies=("c", "a")),
    )
    assert subject.dependency_cycles() == (api.Cycle(("a", "b", "c")),)


def test_self_loop_is_a_single_node_cycle(api):
    subject = graph(api, descriptor(api, "self", dependencies=("self",)))
    assert subject.dependency_cycles() == (api.Cycle(("self",)),)


def test_single_node_without_self_loop_is_not_a_cycle(api):
    subject = graph(api, descriptor(api, "single"))
    assert subject.dependency_cycles() == ()


def test_unresolved_edges_are_excluded_from_scc(api):
    subject = graph(
        api,
        descriptor(api, "a", dependencies=("missing",)),
    )
    assert subject.dependency_cycles() == ()


def test_edges_from_multiple_versions_are_merged_before_scc(api):
    subject = graph(
        api,
        descriptor(api, "a", "v1", ("b",)),
        descriptor(api, "a", "v2", ("b",)),
        descriptor(api, "b", "v1", ("a",)),
        descriptor(api, "b", "v2", ("a",)),
    )
    assert subject.dependency_cycles() == (api.Cycle(("a", "b")),)


def test_multiple_scc_records_are_sorted_and_not_duplicated(api):
    subject = graph(
        api,
        descriptor(api, "z", dependencies=("z",)),
        descriptor(api, "b", dependencies=("a",)),
        descriptor(api, "a", dependencies=("b",)),
    )
    assert subject.dependency_cycles() == (
        api.Cycle(("a", "b")),
        api.Cycle(("z",)),
    )


def test_graph_is_an_isolated_snapshot_of_catalog_list(api):
    catalog = api.Catalog()
    catalog.register(descriptor(api, "source", dependencies=("target",)))
    old_graph = api.Graph(catalog.list())

    catalog.register(descriptor(api, "target"))

    assert old_graph.unresolved_dependencies() == (
        api.Unresolved("source", "v1", "target"),
    )
    assert api.Graph(catalog.list()).unresolved_dependencies() == ()


def test_snapshot_does_not_retain_or_use_catalog_lock(api):
    catalog = api.Catalog()
    catalog.register(descriptor(api, "source"))
    subject = api.Graph(catalog.list())
    assert not hasattr(subject, "_catalog")
    assert subject.direct_dependencies("source", "v1") == ()


def test_duplicate_exact_identity_is_rejected_in_direct_snapshot(api):
    duplicate = descriptor(api, "source", "v1")
    with pytest.raises(ValueError):
        graph(api, duplicate, duplicate)


def test_direct_snapshot_applies_stage61_descriptor_validation(api):
    invalid = descriptor(api, " source")
    with pytest.raises(ValueError):
        graph(api, invalid)


def test_results_and_records_are_immutable(api):
    subject = graph(
        api,
        descriptor(api, "source", dependencies=("missing",)),
    )
    dependencies = subject.direct_dependencies("source", "v1")
    unresolved = subject.unresolved_dependencies()

    assert isinstance(dependencies, tuple)
    assert isinstance(unresolved, tuple)
    with pytest.raises(TypeError):
        dependencies[0] = "changed"
    with pytest.raises(FrozenInstanceError):
        unresolved[0].dependency_asset_id = "changed"


def test_scope_does_not_expose_transitive_or_mutating_operations():
    from core.capabilities.dependency_graph import (
        InMemoryCapabilityDependencyGraph,
    )

    graph = InMemoryCapabilityDependencyGraph(())

    assert hasattr(graph, "potential_transitive_dependents")

    forbidden = (
        "transitive_paths",
        "impact_paths",
        "impact_severity",
        "remove",
        "delete",
        "retire",
        "enforce_removal",
        "resolve",
        "bind",
        "set_lifecycle",
    )
    for name in forbidden:
        assert not hasattr(graph, name)
