from __future__ import annotations

from collections.abc import Iterable

from .catalog import _SchemaRejected, _canonical_descriptor
from .models import (
    CapabilityDescriptor,
    CapabilityIdentity,
    DependencyCycle,
    UnresolvedDependency,
)


def _validated_query_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a clean non-empty string")
    return value


class InMemoryCapabilityDependencyGraph:
    def __init__(
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
