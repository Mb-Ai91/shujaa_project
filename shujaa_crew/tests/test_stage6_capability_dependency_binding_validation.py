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
        BindingDisposition=getattr(
            models,
            "DependencyBindingDisposition",
            None,
        ),
        BindingValidation=getattr(
            models,
            "DependencyBindingValidation",
            None,
        ),
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
        capabilities=("binding-validation-test",),
        lifecycle=lifecycle or api.Lifecycle.ACTIVE,
        dependency_asset_ids=dependencies,
        provenance="local-test",
        risk_tier=None,
        required_permissions=(),
    )


def validate(
    graph,
    asset_id="source",
    version="v1",
    dependency_asset_id="target",
    target_version="v1",
):
    return graph.validate_dependency_binding(
        asset_id,
        version,
        dependency_asset_id,
        target_version,
    )


def expected(api, dependency_asset_id, target_version, disposition):
    return api.BindingValidation(
        dependency_asset_id=dependency_asset_id,
        target_identity=(dependency_asset_id, target_version),
        disposition=getattr(api.BindingDisposition, disposition),
    )


def test_public_binding_models_are_closed_immutable_and_minimal(api):
    assert api.BindingDisposition is not None
    assert api.BindingValidation is not None
    assert tuple(item.value for item in api.BindingDisposition) == (
        "structurally_valid",
        "dependency_not_declared",
        "target_not_found",
    )
    assert tuple(field.name for field in fields(api.BindingValidation)) == (
        "dependency_asset_id",
        "target_identity",
        "disposition",
    )


def test_protocol_and_graph_expose_only_the_approved_query_shape(api):
    method = api.Protocol.validate_dependency_binding
    parameters = signature(method).parameters

    assert tuple(parameters) == (
        "self",
        "asset_id",
        "version",
        "dependency_asset_id",
        "target_version",
    )
    for name in tuple(parameters)[1:]:
        assert parameters[name].default is Parameter.empty
    assert hasattr(api.Graph, "validate_dependency_binding")


@pytest.mark.parametrize(
    ("asset_id", "version", "dependency_asset_id", "target_version", "error"),
    (
        (None, "v1", "target", "v1", TypeError),
        ("source", None, "target", "v1", TypeError),
        ("source", "v1", None, "v1", TypeError),
        ("source", "v1", "target", None, TypeError),
        ("", "v1", "target", "v1", ValueError),
        ("source", " v1", "target", "v1", ValueError),
        ("source", "v1", "target ", "v1", ValueError),
        ("source", "v1", "target", "", ValueError),
    ),
)
def test_invalid_input_uses_existing_validation_contract(
    api,
    asset_id,
    version,
    dependency_asset_id,
    target_version,
    error,
):
    with pytest.raises(error):
        validate(
            api.Graph(()),
            asset_id,
            version,
            dependency_asset_id,
            target_version,
        )


def test_valid_missing_source_returns_none(api):
    assert validate(api.Graph(())) is None


def test_declaration_is_checked_on_exact_source_version_without_union(api):
    graph = api.Graph(
        (
            descriptor(api, "source", version="v1"),
            descriptor(
                api,
                "source",
                version="v2",
                dependencies=("target",),
            ),
            descriptor(api, "target"),
        )
    )

    assert validate(graph, version="v1") == expected(
        api,
        "target",
        "v1",
        "DEPENDENCY_NOT_DECLARED",
    )
    assert validate(graph, version="v2") == expected(
        api,
        "target",
        "v1",
        "STRUCTURALLY_VALID",
    )


@pytest.mark.parametrize(
    "descriptors",
    (
        (),
        ("other-version",),
    ),
)
def test_declared_dependency_with_missing_exact_target_is_not_found(
    api,
    descriptors,
):
    records = [descriptor(api, "source", dependencies=("target",))]
    if descriptors:
        records.append(descriptor(api, "target", version="v2"))
    graph = api.Graph(tuple(records))

    assert validate(graph, target_version="v1") == expected(
        api,
        "target",
        "v1",
        "TARGET_NOT_FOUND",
    )


def test_exact_registered_target_is_structurally_valid_only(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target", version="v2"),
        )
    )

    assert validate(graph, target_version="v2") == expected(
        api,
        "target",
        "v2",
        "STRUCTURALLY_VALID",
    )


def test_structural_validity_matches_slice64_candidates_in_same_snapshot(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target", version="v1"),
            descriptor(api, "target", version="v2"),
        )
    )
    candidates = graph.dependency_resolution_candidates("source", "v1")[0]

    for target_identity in candidates.candidate_identities:
        assert validate(
            graph,
            target_version=target_identity[1],
        ).disposition is api.BindingDisposition.STRUCTURALLY_VALID
    assert validate(graph, target_version="v3").disposition is (
        api.BindingDisposition.TARGET_NOT_FOUND
    )


@pytest.mark.parametrize(
    "lifecycle",
    ("RETIRED", "QUARANTINED"),
)
def test_lifecycle_does_not_filter_structural_validity(api, lifecycle):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(
                api,
                "target",
                lifecycle=getattr(api.Lifecycle, lifecycle),
            ),
        )
    )

    assert validate(graph) == expected(
        api,
        "target",
        "v1",
        "STRUCTURALLY_VALID",
    )


def test_self_dependency_is_structurally_valid_when_identity_exists(api):
    graph = api.Graph(
        (descriptor(api, "source", dependencies=("source",)),)
    )

    assert validate(
        graph,
        dependency_asset_id="source",
        target_version="v1",
    ) == expected(api, "source", "v1", "STRUCTURALLY_VALID")


def test_snapshot_isolation_changes_only_for_new_graph(api):
    catalog = api.Catalog()
    catalog.register(descriptor(api, "source", dependencies=("target",)))
    old_graph = api.Graph(catalog.list())

    assert validate(old_graph) == expected(
        api,
        "target",
        "v1",
        "TARGET_NOT_FOUND",
    )

    catalog.register(descriptor(api, "target"))
    new_graph = api.Graph(catalog.list())

    assert validate(old_graph) == expected(
        api,
        "target",
        "v1",
        "TARGET_NOT_FOUND",
    )
    assert validate(new_graph) == expected(
        api,
        "target",
        "v1",
        "STRUCTURALLY_VALID",
    )


def test_matching_is_exact_and_case_sensitive(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("Target",)),
            descriptor(api, "target", version="v1"),
            descriptor(api, "Target", version="V1"),
        )
    )

    assert validate(
        graph,
        dependency_asset_id="Target",
        target_version="v1",
    ).disposition is api.BindingDisposition.TARGET_NOT_FOUND
    assert validate(
        graph,
        dependency_asset_id="Target",
        target_version="V1",
    ).disposition is api.BindingDisposition.STRUCTURALLY_VALID


def test_query_uses_snapshot_indexes_without_full_rescan(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target"),
        )
    )

    class GetOnlyMapping(dict):
        def __iter__(self):
            raise AssertionError("validation rescanned snapshot records")

        def items(self):
            raise AssertionError("validation rescanned snapshot records")

        def keys(self):
            raise AssertionError("validation rescanned snapshot records")

        def values(self):
            raise AssertionError("validation rescanned snapshot records")

    graph._dependencies_by_identity = GetOnlyMapping(
        graph._dependencies_by_identity
    )
    graph._candidate_identities_by_asset_id = GetOnlyMapping(
        graph._candidate_identities_by_asset_id
    )

    assert validate(graph).disposition is (
        api.BindingDisposition.STRUCTURALLY_VALID
    )


def test_results_are_deterministic_and_immutable(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target"),
        )
    )

    first = validate(graph)
    second = validate(graph)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.disposition = api.BindingDisposition.TARGET_NOT_FOUND


def test_scope_remains_read_only_without_resolver_or_binding_storage(api):
    graph = api.Graph((descriptor(api, "source"),))

    assert hasattr(graph, "validate_dependency_binding")
    for forbidden in (
        "bind_dependency",
        "persist_binding",
        "resolve_dependency",
        "select_candidate",
        "approve_binding",
        "set_lifecycle",
        "remove",
    ):
        assert not hasattr(graph, forbidden)
