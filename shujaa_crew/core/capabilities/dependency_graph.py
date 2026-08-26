from __future__ import annotations

from collections.abc import Iterable
from types import MappingProxyType

from .catalog import _SchemaRejected, _canonical_descriptor
from .models import (
    CapabilityDescriptor,
    CapabilityIdentity,
    DependencyBindingDisposition,
    DependencyBindingPlanIssue,
    DependencyBindingPlanIssueKind,
    DependencyBindingPlanValidation,
    DependencyBindingProposal,
    DependencyBindingValidation,
    DependencyCandidateDisposition,
    DependencyCycle,
    DependencyResolutionCandidates,
    UnresolvedDependency,
)


def _validated_query_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a clean non-empty string")
    return value


_BINDING_PLAN_ISSUE_KIND_ORDER = MappingProxyType(
    {
        DependencyBindingPlanIssueKind.MISSING_BINDING: 0,
        DependencyBindingPlanIssueKind.DUPLICATE_BINDING: 1,
        DependencyBindingPlanIssueKind.CONFLICTING_BINDING: 2,
    }
)


class InMemoryCapabilityDependencyGraph:
    def __init__(
        self,
        descriptors: tuple[CapabilityDescriptor, ...],
    ) -> None:
        self._stage62_init(descriptors)

        reverse: dict[str, set[CapabilityIdentity]] = {}
        for descriptor in descriptors:
            source = (descriptor.asset_id, descriptor.version)
            for dependency_asset_id in descriptor.dependency_asset_ids:
                reverse.setdefault(dependency_asset_id, set()).add(source)

        self._impact_reverse_adjacency = {
            dependency_asset_id: tuple(sorted(identities))
            for dependency_asset_id, identities in reverse.items()
        }

    def _stage62_init(
        self,
        descriptors: tuple[CapabilityDescriptor, ...],
    ) -> None:
        if not isinstance(descriptors, tuple):
            raise TypeError("descriptors must be a tuple snapshot")

        records: dict[CapabilityIdentity, CapabilityDescriptor] = {}
        for candidate in descriptors:
            try:
                descriptor = _canonical_descriptor(candidate)
            except _SchemaRejected as error:
                raise ValueError(str(error)) from error

            identity = (descriptor.asset_id, descriptor.version)
            if identity in records:
                raise ValueError("descriptors contains a duplicate identity")
            records[identity] = descriptor

        identities = tuple(sorted(records))
        asset_ids = frozenset(identity[0] for identity in identities)

        identities_by_asset_id: dict[str, list[CapabilityIdentity]] = {}
        for identity in identities:
            identities_by_asset_id.setdefault(identity[0], []).append(identity)
        self._candidate_identities_by_asset_id = MappingProxyType(
            {
                asset_id: tuple(asset_identities)
                for asset_id, asset_identities in identities_by_asset_id.items()
            }
        )

        dependencies_by_identity = {
            identity: records[identity].dependency_asset_ids
            for identity in identities
        }

        dependents: dict[str, set[CapabilityIdentity]] = {}
        unresolved: list[UnresolvedDependency] = []
        adjacency_sets: dict[str, set[str]] = {
            asset_id: set() for asset_id in asset_ids
        }

        for identity in identities:
            source_asset_id, source_version = identity
            for dependency_asset_id in dependencies_by_identity[identity]:
                dependents.setdefault(dependency_asset_id, set()).add(identity)
                if dependency_asset_id in asset_ids:
                    adjacency_sets[source_asset_id].add(dependency_asset_id)
                else:
                    unresolved.append(
                        UnresolvedDependency(
                            source_asset_id=source_asset_id,
                            source_version=source_version,
                            dependency_asset_id=dependency_asset_id,
                        )
                    )

        self._dependencies_by_identity = dependencies_by_identity
        self._dependents = {
            dependency_asset_id: tuple(sorted(source_identities))
            for dependency_asset_id, source_identities in dependents.items()
        }
        self._unresolved = tuple(
            sorted(
                unresolved,
                key=lambda item: (
                    item.source_asset_id,
                    item.source_version,
                    item.dependency_asset_id,
                ),
            )
        )
        self._adjacency = {
            asset_id: tuple(sorted(targets))
            for asset_id, targets in adjacency_sets.items()
        }
        self._cycles = self._build_cycles()

    def direct_dependencies(
        self,
        asset_id: str,
        version: str,
    ) -> tuple[str, ...] | None:
        identity = (
            _validated_query_string(asset_id, "asset_id"),
            _validated_query_string(version, "version"),
        )
        return self._dependencies_by_identity.get(identity)

    def direct_dependents(
        self,
        dependency_asset_id: str,
    ) -> tuple[CapabilityIdentity, ...]:
        canonical = _validated_query_string(
            dependency_asset_id,
            "dependency_asset_id",
        )
        return self._dependents.get(canonical, ())

    def dependency_resolution_candidates(
        self,
        asset_id: str,
        version: str,
    ) -> tuple[DependencyResolutionCandidates, ...] | None:
        identity = (
            _validated_query_string(asset_id, "asset_id"),
            _validated_query_string(version, "version"),
        )
        dependencies = self._dependencies_by_identity.get(identity)
        if dependencies is None:
            return None

        results: list[DependencyResolutionCandidates] = []
        for dependency_asset_id in dependencies:
            candidates = self._candidate_identities_by_asset_id.get(
                dependency_asset_id,
                (),
            )
            if not candidates:
                disposition = DependencyCandidateDisposition.UNRESOLVED
            elif len(candidates) == 1:
                disposition = DependencyCandidateDisposition.UNIQUE
            else:
                disposition = (
                    DependencyCandidateDisposition.MULTIPLE_CANDIDATES
                )
            results.append(
                DependencyResolutionCandidates(
                    dependency_asset_id=dependency_asset_id,
                    candidate_identities=candidates,
                    disposition=disposition,
                )
            )
        return tuple(results)

    def validate_dependency_binding(
        self,
        asset_id: str,
        version: str,
        dependency_asset_id: str,
        target_version: str,
    ) -> DependencyBindingValidation | None:
        source_identity = (
            _validated_query_string(asset_id, "asset_id"),
            _validated_query_string(version, "version"),
        )
        canonical_dependency_asset_id = _validated_query_string(
            dependency_asset_id,
            "dependency_asset_id",
        )
        target_identity = (
            canonical_dependency_asset_id,
            _validated_query_string(target_version, "target_version"),
        )

        dependencies = self._dependencies_by_identity.get(source_identity)
        if dependencies is None:
            return None

        if canonical_dependency_asset_id not in dependencies:
            disposition = (
                DependencyBindingDisposition.DEPENDENCY_NOT_DECLARED
            )
        elif target_identity not in self._candidate_identities_by_asset_id.get(
            canonical_dependency_asset_id,
            (),
        ):
            disposition = DependencyBindingDisposition.TARGET_NOT_FOUND
        else:
            disposition = DependencyBindingDisposition.STRUCTURALLY_VALID

        return DependencyBindingValidation(
            dependency_asset_id=canonical_dependency_asset_id,
            target_identity=target_identity,
            disposition=disposition,
        )

    def validate_dependency_binding_plan(
        self,
        asset_id: str,
        version: str,
        bindings: tuple[DependencyBindingProposal, ...],
    ) -> DependencyBindingPlanValidation | None:
        source_identity = (
            _validated_query_string(asset_id, "asset_id"),
            _validated_query_string(version, "version"),
        )
        if not isinstance(bindings, tuple):
            raise TypeError("bindings must be a tuple")

        canonical_bindings: list[tuple[str, str]] = []
        for binding in bindings:
            if not isinstance(binding, DependencyBindingProposal):
                raise TypeError(
                    "bindings must contain DependencyBindingProposal items"
                )
            canonical_bindings.append(
                (
                    _validated_query_string(
                        binding.dependency_asset_id,
                        "dependency_asset_id",
                    ),
                    _validated_query_string(
                        binding.target_version,
                        "target_version",
                    ),
                )
            )

        dependencies = self._dependencies_by_identity.get(source_identity)
        if dependencies is None:
            return None

        grouped: dict[str, list[str]] = {}
        for dependency_asset_id, target_version in canonical_bindings:
            grouped.setdefault(dependency_asset_id, []).append(target_version)

        binding_validations: list[DependencyBindingValidation] = []
        for dependency_asset_id, target_version in sorted(
            set(canonical_bindings)
        ):
            validation = self.validate_dependency_binding(
                source_identity[0],
                source_identity[1],
                dependency_asset_id,
                target_version,
            )
            if validation is None:
                raise AssertionError("source disappeared from immutable snapshot")
            binding_validations.append(validation)

        issues: list[DependencyBindingPlanIssue] = []
        for dependency_asset_id in dependencies:
            if dependency_asset_id not in grouped:
                issues.append(
                    DependencyBindingPlanIssue(
                        dependency_asset_id=dependency_asset_id,
                        kind=DependencyBindingPlanIssueKind.MISSING_BINDING,
                        target_versions=(),
                    )
                )

        declared_dependencies = frozenset(dependencies)
        for dependency_asset_id, target_versions in grouped.items():
            if dependency_asset_id not in declared_dependencies:
                continue
            distinct_versions = tuple(sorted(set(target_versions)))
            if len(distinct_versions) > 1:
                issues.append(
                    DependencyBindingPlanIssue(
                        dependency_asset_id=dependency_asset_id,
                        kind=(
                            DependencyBindingPlanIssueKind.CONFLICTING_BINDING
                        ),
                        target_versions=distinct_versions,
                    )
                )
            elif len(target_versions) > 1:
                issues.append(
                    DependencyBindingPlanIssue(
                        dependency_asset_id=dependency_asset_id,
                        kind=DependencyBindingPlanIssueKind.DUPLICATE_BINDING,
                        target_versions=distinct_versions,
                    )
                )

        ordered_issues = tuple(
            sorted(
                issues,
                key=lambda item: (
                    item.dependency_asset_id,
                    _BINDING_PLAN_ISSUE_KIND_ORDER[item.kind],
                    item.target_versions,
                ),
            )
        )
        ordered_validations = tuple(binding_validations)
        structurally_complete = (
            not ordered_issues
            and all(
                validation.disposition
                is DependencyBindingDisposition.STRUCTURALLY_VALID
                for validation in ordered_validations
            )
        )

        return DependencyBindingPlanValidation(
            source_identity=source_identity,
            binding_validations=ordered_validations,
            issues=ordered_issues,
            structurally_complete=structurally_complete,
        )

    def unresolved_dependencies(
        self,
    ) -> tuple[UnresolvedDependency, ...]:
        return self._unresolved

    def dependency_cycles(self) -> tuple[DependencyCycle, ...]:
        return self._cycles

    def _build_cycles(self) -> tuple[DependencyCycle, ...]:
        finish_order = self._finish_order()
        reverse: dict[str, list[str]] = {
            asset_id: [] for asset_id in self._adjacency
        }
        for source, targets in self._adjacency.items():
            for target in targets:
                reverse[target].append(source)

        visited: set[str] = set()
        cycles: list[DependencyCycle] = []
        for start in reversed(finish_order):
            if start in visited:
                continue

            component: list[str] = []
            stack = [start]
            visited.add(start)
            while stack:
                node = stack.pop()
                component.append(node)
                for neighbour in reverse[node]:
                    if neighbour not in visited:
                        visited.add(neighbour)
                        stack.append(neighbour)

            ordered = tuple(sorted(component))
            if len(ordered) > 1 or ordered[0] in self._adjacency[ordered[0]]:
                cycles.append(DependencyCycle(asset_ids=ordered))

        return tuple(sorted(cycles, key=lambda item: item.asset_ids))

    def _finish_order(self) -> tuple[str, ...]:
        visited: set[str] = set()
        finished: list[str] = []

        for start in sorted(self._adjacency):
            if start in visited:
                continue

            visited.add(start)
            stack: list[tuple[str, Iterable[str]]] = [
                (start, iter(self._adjacency[start]))
            ]
            while stack:
                node, neighbours = stack[-1]
                try:
                    neighbour = next(neighbours)
                except StopIteration:
                    finished.append(node)
                    stack.pop()
                    continue

                if neighbour not in visited:
                    visited.add(neighbour)
                    stack.append(
                        (neighbour, iter(self._adjacency[neighbour]))
                    )

        return tuple(finished)

    def potential_transitive_dependents(
        self,
        dependency_asset_id: str,
    ) -> tuple[CapabilityIdentity, ...]:
        target = _validated_query_string(
            dependency_asset_id,
            "dependency_asset_id",
        )

        impacted: set[CapabilityIdentity] = set()
        visited_asset_ids = {target}
        pending = [target]

        while pending:
            current = pending.pop()
            for identity in self._impact_reverse_adjacency.get(
                current,
                (),
            ):
                source_asset_id, _ = identity

                if source_asset_id != target:
                    impacted.add(identity)

                if source_asset_id not in visited_asset_ids:
                    visited_asset_ids.add(source_asset_id)
                    pending.append(source_asset_id)

        return tuple(sorted(impacted))
