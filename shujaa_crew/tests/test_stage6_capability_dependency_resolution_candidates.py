from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from inspect import Parameter, signature
from types import SimpleNamespace

import pytest


@pytest.fixture
def api():
    from core.capabilities.catalog import InMemoryCapabilityCatalog
    from core.capabilities.contracts import CapabilityDependencyGraphProtocol
    from core.capabilities.dependency_graph import InMemoryCapabilityDependencyGraph
    from core.capabilities import models

    return SimpleNamespace(
        AssetType=models.CapabilityAssetType,
        CandidateDisposition=getattr(
            models,
            "DependencyCandidateDisposition",
            None,
        ),
        Candidates=getattr(models, "DependencyResolutionCandidates", None),
        Catalog=InMemoryCapabilityCatalog,
        Descriptor=models.CapabilityDescriptor,
        Graph=InMemoryCapabilityDependencyGraph,
        Lifecycle=models.CapabilityLifecycle,
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
        capabilities=("resolution-candidate-test",),
        lifecycle=lifecycle or api.Lifecycle.ACTIVE,
        dependency_asset_ids=dependencies,
        provenance="local-test",
        risk_tier=None,
        required_permissions=(),
    )


def resolution_candidates(graph, asset_id, version="v1"):
    return graph.dependency_resolution_candidates(asset_id, version)


def expected(api, dependency_asset_id, identities, disposition):
    return api.Candidates(
        dependency_asset_id=dependency_asset_id,
        candidate_identities=identities,
        disposition=getattr(api.CandidateDisposition, disposition),
    )


def test_public_candidate_models_are_closed_and_minimal(api):
    assert api.CandidateDisposition is not None
    assert api.Candidates is not None
    assert tuple(item.value for item in api.CandidateDisposition) == (
        "unresolved",
        "unique",
        "multiple_candidates",
    )
    assert tuple(field.name for field in fields(api.Candidates)) == (
        "dependency_asset_id",
        "candidate_identities",
        "disposition",
    )


def test_protocol_and_graph_expose_only_the_approved_query_shape(api):
    method = api.Protocol.dependency_resolution_candidates
    parameters = signature(method).parameters

    assert tuple(parameters) == ("self", "asset_id", "version")
    assert parameters["asset_id"].default is Parameter.empty
    assert parameters["version"].default is Parameter.empty
    assert hasattr(api.Graph, "dependency_resolution_candidates")


@pytest.mark.parametrize(
    ("asset_id", "version", "error"),
    (
        (None, "v1", TypeError),
        ("source", None, TypeError),
        ("", "v1", ValueError),
        ("source", " v1", ValueError),
    ),
)
def test_invalid_input_uses_existing_validation_not_missing_source(
    api,
    asset_id,
    version,
    error,
):
    graph = api.Graph(())

    with pytest.raises(error):
        resolution_candidates(graph, asset_id, version)


def test_valid_missing_source_returns_none(api):
    assert resolution_candidates(api.Graph(()), "missing", "v1") is None


def test_existing_source_without_dependencies_returns_empty_tuple(api):
    graph = api.Graph((descriptor(api, "source"),))

    assert resolution_candidates(graph, "source") == ()


def test_unregistered_dependency_is_unresolved(api):
    graph = api.Graph(
        (descriptor(api, "source", dependencies=("missing",)),)
    )

    assert resolution_candidates(graph, "source") == (
        expected(api, "missing", (), "UNRESOLVED"),
    )


def test_one_registered_identity_is_unique_but_not_selected(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target", version="v2"),
        )
    )

    assert resolution_candidates(graph, "source") == (
        expected(api, "target", (("target", "v2"),), "UNIQUE"),
    )
    assert tuple(field.name for field in fields(api.Candidates)) == (
        "dependency_asset_id",
        "candidate_identities",
        "disposition",
    )


def test_multiple_registered_versions_are_all_candidates_and_sorted(api):
    graph = api.Graph(
        (
            descriptor(api, "target", version="v3"),
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target", version="v1"),
            descriptor(api, "target", version="v2"),
        )
    )

    assert resolution_candidates(graph, "source") == (
        expected(
            api,
            "target",
            (("target", "v1"), ("target", "v2"), ("target", "v3")),
            "MULTIPLE_CANDIDATES",
        ),
    )


def test_every_registered_lifecycle_state_remains_a_candidate(api):
    descriptors = [descriptor(api, "source", dependencies=("target",))]
    for index, lifecycle in enumerate(api.Lifecycle, start=1):
        descriptors.append(
            descriptor(
                api,
                "target",
                version=f"v{index}",
                lifecycle=lifecycle,
            )
        )
    graph = api.Graph(tuple(descriptors))

    assert resolution_candidates(graph, "source") == (
        expected(
            api,
            "target",
            tuple(("target", f"v{index}") for index in range(1, 7)),
            "MULTIPLE_CANDIDATES",
        ),
    )


def test_dependency_records_are_deduplicated_and_sorted(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("zeta", "alpha")),
            descriptor(api, "alpha"),
        )
    )

    assert resolution_candidates(graph, "source") == (
        expected(api, "alpha", (("alpha", "v1"),), "UNIQUE"),
        expected(api, "zeta", (), "UNRESOLVED"),
    )


def test_candidate_matching_is_exact_and_case_sensitive(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("Target",)),
            descriptor(api, "target", version="v1"),
            descriptor(api, "Target-extra", version="v1"),
        )
    )

    assert resolution_candidates(graph, "source") == (
        expected(api, "Target", (), "UNRESOLVED"),
    )


def test_graph_keeps_candidate_snapshot_isolated_from_catalog(api):
    catalog = api.Catalog()
    catalog.register(descriptor(api, "source", dependencies=("target",)))
    catalog.register(descriptor(api, "target", version="v1"))
    graph = api.Graph(catalog.list())

    catalog.register(descriptor(api, "target", version="v2"))

    assert resolution_candidates(graph, "source") == (
        expected(api, "target", (("target", "v1"),), "UNIQUE"),
    )


def test_candidate_query_uses_prebuilt_index_without_identity_rescan(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target", version="v1"),
        )
    )

    class NoIdentityScan(dict):
        def __iter__(self):
            raise AssertionError("query rescanned identity records")

        def items(self):
            raise AssertionError("query rescanned identity records")

        def keys(self):
            raise AssertionError("query rescanned identity records")

        def values(self):
            raise AssertionError("query rescanned identity records")

    graph._dependencies_by_identity = NoIdentityScan(
        graph._dependencies_by_identity
    )

    assert resolution_candidates(graph, "source") == (
        expected(api, "target", (("target", "v1"),), "UNIQUE"),
    )


def test_results_and_candidate_records_are_immutable(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target"),
        )
    )
    result = resolution_candidates(graph, "source")

    assert isinstance(result, tuple)
    assert isinstance(result[0].candidate_identities, tuple)
    with pytest.raises(FrozenInstanceError):
        result[0].disposition = api.CandidateDisposition.UNRESOLVED


def test_scope_stays_read_only_and_does_not_become_a_resolver(api):
    graph = api.Graph((descriptor(api, "source"),))

    assert hasattr(graph, "dependency_resolution_candidates")
    for forbidden in (
        "resolve_dependency",
        "select_candidate",
        "bind_dependency",
        "approve_candidate",
        "set_lifecycle",
        "remove",
    ):
        assert not hasattr(graph, forbidden)
