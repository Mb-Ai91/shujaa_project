from __future__ import annotations

from inspect import Parameter, signature
from types import SimpleNamespace

import pytest


@pytest.fixture
def api():
    from core.capabilities.contracts import CapabilityDependencyGraphProtocol
    from core.capabilities.dependency_graph import (
        InMemoryCapabilityDependencyGraph,
    )
    from core.capabilities.models import (
        CapabilityAssetType,
        CapabilityDescriptor,
        CapabilityLifecycle,
    )

    return SimpleNamespace(
        AssetType=CapabilityAssetType,
        Descriptor=CapabilityDescriptor,
        Graph=InMemoryCapabilityDependencyGraph,
        Lifecycle=CapabilityLifecycle,
        Protocol=CapabilityDependencyGraphProtocol,
    )


def descriptor(
    api,
    asset_id,
    *,
    version="v1",
    dependencies=(),
    lifecycle=None,
):
    return api.Descriptor(
        asset_id=asset_id,
        version=version,
        asset_type=api.AssetType.AGENT,
        capabilities=("impact-test",),
        lifecycle=lifecycle or api.Lifecycle.ACTIVE,
        dependency_asset_ids=dependencies,
        provenance="local-test",
        risk_tier=None,
        required_permissions=(),
    )


def impact(graph, dependency_asset_id):
    return graph.potential_transitive_dependents(dependency_asset_id)


def test_protocol_exposes_approved_impact_query(api):
    method = api.Protocol.potential_transitive_dependents
    parameters = signature(method).parameters

    assert tuple(parameters) == ("self", "dependency_asset_id")
    assert parameters["dependency_asset_id"].default is Parameter.empty
    assert hasattr(api.Graph, "potential_transitive_dependents")


def test_unregistered_target_is_still_analyzed(api):
    graph = api.Graph(
        (
            descriptor(
                api,
                "consumer",
                dependencies=("unregistered-target",),
            ),
        )
    )

    assert impact(graph, "unregistered-target") == (("consumer", "v1"),)


def test_transitive_dependents_cross_multiple_levels(api):
    graph = api.Graph(
        (
            descriptor(api, "a", dependencies=("target",)),
            descriptor(api, "b", dependencies=("a",)),
            descriptor(api, "c", dependencies=("b",)),
        )
    )

    assert impact(graph, "target") == (
        ("a", "v1"),
        ("b", "v1"),
        ("c", "v1"),
    )


def test_only_declaring_version_is_emitted_then_asset_id_propagates(api):
    graph = api.Graph(
        (
            descriptor(
                api,
                "adapter",
                version="v1",
                dependencies=("target",),
            ),
            descriptor(api, "adapter", version="v2"),
            descriptor(api, "parent", dependencies=("adapter",)),
        )
    )

    assert impact(graph, "target") == (
        ("adapter", "v1"),
        ("parent", "v1"),
    )


def test_all_declaring_versions_are_emitted_without_duplicate_parent(api):
    graph = api.Graph(
        (
            descriptor(
                api,
                "adapter",
                version="v1",
                dependencies=("target",),
            ),
            descriptor(
                api,
                "adapter",
                version="v2",
                dependencies=("target",),
            ),
            descriptor(api, "parent", dependencies=("adapter",)),
        )
    )

    assert impact(graph, "target") == (
        ("adapter", "v1"),
        ("adapter", "v2"),
        ("parent", "v1"),
    )


def test_all_target_versions_are_excluded_while_traversal_remains_complete(api):
    graph = api.Graph(
        (
            descriptor(api, "target", version="v1", dependencies=("a",)),
            descriptor(api, "target", version="v2"),
            descriptor(api, "a", dependencies=("target",)),
            descriptor(api, "parent", dependencies=("a",)),
        )
    )

    result = impact(graph, "target")

    assert result == (("a", "v1"), ("parent", "v1"))
    assert all(asset_id != "target" for asset_id, _ in result)


def test_cycles_terminate_without_readding_or_reexpanding_target(api):
    graph = api.Graph(
        (
            descriptor(api, "target", dependencies=("a",)),
            descriptor(api, "a", dependencies=("target",)),
            descriptor(api, "b", dependencies=("a",)),
            descriptor(api, "c", dependencies=("b", "target")),
        )
    )

    assert impact(graph, "target") == (
        ("a", "v1"),
        ("b", "v1"),
        ("c", "v1"),
    )


def test_lifecycle_does_not_filter_impact(api):
    graph = api.Graph(
        (
            descriptor(
                api,
                "retired-source",
                dependencies=("target",),
                lifecycle=api.Lifecycle.RETIRED,
            ),
            descriptor(
                api,
                "quarantined-source",
                dependencies=("target",),
                lifecycle=api.Lifecycle.QUARANTINED,
            ),
            descriptor(
                api,
                "parent",
                dependencies=("retired-source",),
                lifecycle=api.Lifecycle.SANDBOX,
            ),
        )
    )

    assert impact(graph, "target") == (
        ("parent", "v1"),
        ("quarantined-source", "v1"),
        ("retired-source", "v1"),
    )


def test_results_are_immutable_deduplicated_and_deterministic(api):
    descriptors = (
        descriptor(api, "z", dependencies=("target",)),
        descriptor(api, "a", dependencies=("target",)),
        descriptor(api, "m", dependencies=("a", "z")),
    )

    first = impact(api.Graph(descriptors), "target")
    second = impact(api.Graph(tuple(reversed(descriptors))), "target")

    assert isinstance(first, tuple)
    assert first == second == (
        ("a", "v1"),
        ("m", "v1"),
        ("z", "v1"),
    )
    assert len(first) == len(set(first))


def test_matching_remains_exact_and_case_sensitive(api):
    graph = api.Graph(
        (
            descriptor(api, "lower", dependencies=("target",)),
            descriptor(api, "upper", dependencies=("Target",)),
        )
    )

    assert impact(graph, "target") == (("lower", "v1"),)
    assert impact(graph, "Target") == (("upper", "v1"),)


def test_validation_matches_existing_direct_dependent_query(api):
    graph = api.Graph(())

    for invalid in (None, "", " target "):
        try:
            graph.direct_dependents(invalid)
        except Exception as expected:
            with pytest.raises(type(expected)):
                impact(graph, invalid)
        else:
            assert impact(graph, invalid) == ()


def test_deep_chain_uses_iterative_traversal(api):
    depth = 1500
    descriptors = tuple(
        descriptor(
            api,
            f"node-{index:04d}",
            dependencies=(
                ("target",)
                if index == 0
                else (f"node-{index - 1:04d}",)
            ),
        )
        for index in range(depth)
    )

    result = impact(api.Graph(descriptors), "target")

    assert len(result) == depth
    assert result[0] == ("node-0000", "v1")
    assert result[-1] == ("node-1499", "v1")


def test_traversal_uses_snapshot_reverse_adjacency_not_public_rescans(
    api,
    monkeypatch,
):
    graph = api.Graph(
        (
            descriptor(api, "a", dependencies=("target",)),
            descriptor(api, "b", dependencies=("a",)),
        )
    )

    def forbidden_rescan(*args, **kwargs):
        raise AssertionError(
            "impact traversal must use reverse adjacency built at snapshot time"
        )

    monkeypatch.setattr(graph, "direct_dependents", forbidden_rescan)

    assert impact(graph, "target") == (("a", "v1"), ("b", "v1"))


def test_scope_remains_read_only_without_paths_policy_or_enforcement(api):
    graph = api.Graph(
        (descriptor(api, "consumer", dependencies=("target",)),)
    )

    assert impact(graph, "target") == (("consumer", "v1"),)

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
