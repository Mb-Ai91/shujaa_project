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
        BindingDisposition=models.DependencyBindingDisposition,
        BindingValidation=models.DependencyBindingValidation,
        Catalog=InMemoryCapabilityCatalog,
        Descriptor=models.CapabilityDescriptor,
        Graph=InMemoryCapabilityDependencyGraph,
        Lifecycle=models.CapabilityLifecycle,
        PlanIssue=getattr(models, "DependencyBindingPlanIssue", None),
        PlanIssueKind=getattr(
            models,
            "DependencyBindingPlanIssueKind",
            None,
        ),
        PlanValidation=getattr(
            models,
            "DependencyBindingPlanValidation",
            None,
        ),
        Proposal=getattr(models, "DependencyBindingProposal", None),
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
        capabilities=("binding-plan-validation-test",),
        lifecycle=lifecycle or api.Lifecycle.ACTIVE,
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


def validate_plan(
    graph,
    bindings,
    *,
    asset_id="source",
    version="v1",
):
    return graph.validate_dependency_binding_plan(
        asset_id,
        version,
        bindings,
    )


def binding_expected(api, dependency_asset_id, target_version, disposition):
    return api.BindingValidation(
        dependency_asset_id=dependency_asset_id,
        target_identity=(dependency_asset_id, target_version),
        disposition=getattr(api.BindingDisposition, disposition),
    )


def issue_expected(api, dependency_asset_id, kind, target_versions):
    return api.PlanIssue(
        dependency_asset_id=dependency_asset_id,
        kind=getattr(api.PlanIssueKind, kind),
        target_versions=target_versions,
    )


def test_public_plan_models_are_closed_immutable_and_minimal(api):
    assert api.Proposal is not None
    assert api.PlanIssueKind is not None
    assert api.PlanIssue is not None
    assert api.PlanValidation is not None
    assert tuple(item.value for item in api.PlanIssueKind) == (
        "missing_binding",
        "duplicate_binding",
        "conflicting_binding",
    )
    assert tuple(field.name for field in fields(api.Proposal)) == (
        "dependency_asset_id",
        "target_version",
    )
    assert tuple(field.name for field in fields(api.PlanIssue)) == (
        "dependency_asset_id",
        "kind",
        "target_versions",
    )
    assert tuple(field.name for field in fields(api.PlanValidation)) == (
        "source_identity",
        "binding_validations",
        "issues",
        "structurally_complete",
    )


def test_public_exports_include_only_the_approved_plan_types(api):
    import core.capabilities as capabilities

    assert capabilities.DependencyBindingProposal is api.Proposal
    assert capabilities.DependencyBindingPlanIssueKind is api.PlanIssueKind
    assert capabilities.DependencyBindingPlanIssue is api.PlanIssue
    assert capabilities.DependencyBindingPlanValidation is api.PlanValidation


def test_protocol_and_graph_expose_only_the_approved_query_shape(api):
    method = api.Protocol.validate_dependency_binding_plan
    parameters = signature(method).parameters

    assert tuple(parameters) == (
        "self",
        "asset_id",
        "version",
        "bindings",
    )
    for name in tuple(parameters)[1:]:
        assert parameters[name].default is Parameter.empty
    assert hasattr(api.Graph, "validate_dependency_binding_plan")


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
def test_invalid_plan_input_precedes_missing_source(
    api,
    asset_id,
    version,
    bindings,
    error,
):
    with pytest.raises(error):
        validate_plan(
            api.Graph(()),
            bindings,
            asset_id=asset_id,
            version=version,
        )


@pytest.mark.parametrize(
    ("dependency_asset_id", "target_version", "error"),
    (
        (None, "v1", TypeError),
        ("target", None, TypeError),
        ("", "v1", ValueError),
        ("target ", "v1", ValueError),
        ("target", "", ValueError),
        ("target", " v1", ValueError),
    ),
)
def test_invalid_proposal_fields_use_existing_string_contract(
    api,
    dependency_asset_id,
    target_version,
    error,
):
    invalid = api.Proposal(
        dependency_asset_id=dependency_asset_id,
        target_version=target_version,
    )

    with pytest.raises(error):
        validate_plan(api.Graph(()), (invalid,))


def test_valid_missing_source_returns_none(api):
    assert validate_plan(api.Graph(()), ()) is None


def test_source_without_dependencies_and_empty_plan_is_complete(api):
    result = validate_plan(
        api.Graph((descriptor(api, "source"),)),
        (),
    )

    assert result == api.PlanValidation(
        source_identity=("source", "v1"),
        binding_validations=(),
        issues=(),
        structurally_complete=True,
    )


def test_missing_binding_is_reported_once(api):
    result = validate_plan(
        api.Graph(
            (
                descriptor(api, "source", dependencies=("alpha", "beta")),
                descriptor(api, "alpha"),
                descriptor(api, "beta"),
            )
        ),
        (proposal(api, "alpha"),),
    )

    assert result.binding_validations == (
        binding_expected(api, "alpha", "v1", "STRUCTURALLY_VALID"),
    )
    assert result.issues == (
        issue_expected(api, "beta", "MISSING_BINDING", ()),
    )
    assert result.structurally_complete is False


def test_undeclared_binding_uses_slice65_result_without_plan_issue(api):
    result = validate_plan(
        api.Graph(
            (
                descriptor(api, "source"),
                descriptor(api, "extra", version="v1"),
                descriptor(api, "extra", version="v2"),
            )
        ),
        (
            proposal(api, "extra", "v2"),
            proposal(api, "extra", "v1"),
            proposal(api, "extra", "v2"),
        ),
    )

    assert result.binding_validations == (
        binding_expected(
            api,
            "extra",
            "v1",
            "DEPENDENCY_NOT_DECLARED",
        ),
        binding_expected(
            api,
            "extra",
            "v2",
            "DEPENDENCY_NOT_DECLARED",
        ),
    )
    assert result.issues == ()
    assert result.structurally_complete is False


def test_identical_duplicates_produce_one_issue_and_one_validation(api):
    repeated = proposal(api, "target", "v2")
    result = validate_plan(
        api.Graph(
            (
                descriptor(api, "source", dependencies=("target",)),
                descriptor(api, "target", version="v2"),
            )
        ),
        (repeated, repeated, repeated),
    )

    assert result.binding_validations == (
        binding_expected(api, "target", "v2", "STRUCTURALLY_VALID"),
    )
    assert result.issues == (
        issue_expected(api, "target", "DUPLICATE_BINDING", ("v2",)),
    )
    assert result.structurally_complete is False


def test_different_targets_produce_one_conflict_only_despite_multiplicity(api):
    result = validate_plan(
        api.Graph(
            (
                descriptor(api, "source", dependencies=("target",)),
                descriptor(api, "target", version="v1"),
                descriptor(api, "target", version="v2"),
            )
        ),
        (
            proposal(api, "target", "v2"),
            proposal(api, "target", "v1"),
            proposal(api, "target", "v2"),
        ),
    )

    assert result.binding_validations == (
        binding_expected(api, "target", "v1", "STRUCTURALLY_VALID"),
        binding_expected(api, "target", "v2", "STRUCTURALLY_VALID"),
    )
    assert result.issues == (
        issue_expected(
            api,
            "target",
            "CONFLICTING_BINDING",
            ("v1", "v2"),
        ),
    )
    assert result.structurally_complete is False


def test_all_independent_problems_are_returned_deterministically(api):
    graph = api.Graph(
        (
            descriptor(
                api,
                "source",
                dependencies=("missing", "duplicate", "conflict", "absent"),
            ),
            descriptor(api, "duplicate"),
            descriptor(api, "conflict", version="v1"),
        )
    )
    bindings = (
        proposal(api, "undeclared"),
        proposal(api, "conflict", "v2"),
        proposal(api, "duplicate"),
        proposal(api, "conflict", "v1"),
        proposal(api, "duplicate"),
        proposal(api, "absent"),
    )

    result = validate_plan(graph, bindings)

    assert result.binding_validations == (
        binding_expected(api, "absent", "v1", "TARGET_NOT_FOUND"),
        binding_expected(api, "conflict", "v1", "STRUCTURALLY_VALID"),
        binding_expected(api, "conflict", "v2", "TARGET_NOT_FOUND"),
        binding_expected(api, "duplicate", "v1", "STRUCTURALLY_VALID"),
        binding_expected(api, "undeclared", "v1", "DEPENDENCY_NOT_DECLARED"),
    )
    assert result.issues == (
        issue_expected(
            api,
            "conflict",
            "CONFLICTING_BINDING",
            ("v1", "v2"),
        ),
        issue_expected(
            api,
            "duplicate",
            "DUPLICATE_BINDING",
            ("v1",),
        ),
        issue_expected(api, "missing", "MISSING_BINDING", ()),
    )
    assert result.structurally_complete is False


def test_complete_plan_is_structural_only(api):
    result = validate_plan(
        api.Graph(
            (
                descriptor(api, "source", dependencies=("alpha", "beta")),
                descriptor(api, "alpha", lifecycle=api.Lifecycle.RETIRED),
                descriptor(api, "beta", lifecycle=api.Lifecycle.QUARANTINED),
            )
        ),
        (
            proposal(api, "beta"),
            proposal(api, "alpha"),
        ),
    )

    assert result.binding_validations == (
        binding_expected(api, "alpha", "v1", "STRUCTURALLY_VALID"),
        binding_expected(api, "beta", "v1", "STRUCTURALLY_VALID"),
    )
    assert result.issues == ()
    assert result.structurally_complete is True
    for forbidden in (
        "approved",
        "authorized",
        "eligible",
        "selected",
        "resolved",
        "persisted",
        "executable",
    ):
        assert not hasattr(result, forbidden)


def test_exact_source_version_is_used_without_dependency_union(api):
    graph = api.Graph(
        (
            descriptor(api, "source", version="v1", dependencies=("alpha",)),
            descriptor(api, "source", version="v2", dependencies=("beta",)),
            descriptor(api, "alpha"),
            descriptor(api, "beta"),
        )
    )

    result = validate_plan(
        graph,
        (proposal(api, "beta"),),
        version="v1",
    )

    assert result.binding_validations == (
        binding_expected(
            api,
            "beta",
            "v1",
            "DEPENDENCY_NOT_DECLARED",
        ),
    )
    assert result.issues == (
        issue_expected(api, "alpha", "MISSING_BINDING", ()),
    )
    assert result.structurally_complete is False


def test_self_dependency_is_handled_structurally(api):
    result = validate_plan(
        api.Graph(
            (
                descriptor(api, "source", dependencies=("source",)),
            )
        ),
        (proposal(api, "source"),),
    )

    assert result.binding_validations == (
        binding_expected(api, "source", "v1", "STRUCTURALLY_VALID"),
    )
    assert result.issues == ()
    assert result.structurally_complete is True


def test_snapshot_isolation_changes_only_for_new_graph(api):
    catalog = api.Catalog()
    catalog.register(descriptor(api, "source", dependencies=("target",)))
    old_graph = api.Graph(catalog.list())
    requested = (proposal(api, "target"),)

    before = validate_plan(old_graph, requested)
    catalog.register(descriptor(api, "target"))
    after_on_old = validate_plan(old_graph, requested)
    after_on_new = validate_plan(api.Graph(catalog.list()), requested)

    assert before == after_on_old
    assert before.binding_validations == (
        binding_expected(api, "target", "v1", "TARGET_NOT_FOUND"),
    )
    assert before.structurally_complete is False
    assert after_on_new.binding_validations == (
        binding_expected(api, "target", "v1", "STRUCTURALLY_VALID"),
    )
    assert after_on_new.structurally_complete is True


def test_each_unique_pair_is_validated_once(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target", version="v1"),
            descriptor(api, "target", version="v2"),
        )
    )
    original = graph.validate_dependency_binding
    calls = []

    def tracking(asset_id, version, dependency_asset_id, target_version):
        calls.append(
            (asset_id, version, dependency_asset_id, target_version)
        )
        return original(
            asset_id,
            version,
            dependency_asset_id,
            target_version,
        )

    graph.validate_dependency_binding = tracking

    validate_plan(
        graph,
        (
            proposal(api, "target", "v2"),
            proposal(api, "target", "v1"),
            proposal(api, "target", "v2"),
            proposal(api, "target", "v1"),
        ),
    )

    assert calls == [
        ("source", "v1", "target", "v1"),
        ("source", "v1", "target", "v2"),
    ]


def test_query_uses_snapshot_indexes_without_full_rescan(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("target",)),
            descriptor(api, "target"),
        )
    )

    class GetOnlyMapping:
        def __init__(self, values):
            self._values = values

        def get(self, key, default=None):
            return self._values.get(key, default)

        def __iter__(self):
            raise AssertionError("plan validation rescanned snapshot records")

        def items(self):
            raise AssertionError("plan validation rescanned snapshot records")

        def keys(self):
            raise AssertionError("plan validation rescanned snapshot records")

        def values(self):
            raise AssertionError("plan validation rescanned snapshot records")

    graph._dependencies_by_identity = GetOnlyMapping(
        graph._dependencies_by_identity
    )
    graph._candidate_identities_by_asset_id = GetOnlyMapping(
        graph._candidate_identities_by_asset_id
    )

    result = validate_plan(graph, (proposal(api, "target"),))
    assert result.structurally_complete is True


def test_results_are_deterministic_and_immutable(api):
    graph = api.Graph(
        (
            descriptor(api, "source", dependencies=("alpha", "beta")),
            descriptor(api, "alpha", version="v1"),
            descriptor(api, "alpha", version="v2"),
            descriptor(api, "beta"),
        )
    )
    left = (
        proposal(api, "beta"),
        proposal(api, "alpha", "v2"),
        proposal(api, "alpha", "v1"),
    )
    right = tuple(reversed(left))

    first = validate_plan(graph, left)
    second = validate_plan(graph, right)

    assert first == second
    assert isinstance(first.binding_validations, tuple)
    assert isinstance(first.issues, tuple)
    assert isinstance(first.issues[0].target_versions, tuple)
    with pytest.raises(FrozenInstanceError):
        first.structurally_complete = True
    with pytest.raises(FrozenInstanceError):
        first.issues[0].kind = api.PlanIssueKind.DUPLICATE_BINDING
    with pytest.raises(FrozenInstanceError):
        left[0].target_version = "v9"


def test_scope_remains_read_only_without_resolver_or_plan_storage(api):
    graph = api.Graph((descriptor(api, "source"),))

    assert hasattr(graph, "validate_dependency_binding_plan")
    for forbidden in (
        "save_binding_plan",
        "persist_binding_plan",
        "bind_dependencies",
        "resolve_dependencies",
        "select_candidates",
        "approve_binding_plan",
        "set_lifecycle",
        "remove",
    ):
        assert not hasattr(graph, forbidden)
