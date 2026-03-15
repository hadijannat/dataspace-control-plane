"""Pack resolver — dependency graph, conflict detection, ResolvedPackProfile.

The resolver takes a set of requested pack activations and produces a
``ResolvedPackProfile`` that is safe to apply to a tenant/legal-entity/environment.

Conflict and dependency checking is done at resolve time, not at load time,
so that individual pack units can be loaded independently.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ._shared.capabilities import PackCapability
from ._shared.errors import PackConflictError, PackDependencyError, PackVersionError
from ._shared.manifest import PackManifest
from ._shared.versioning import versions_compatible
from .registry import PackRegistry

logger = logging.getLogger(__name__)


@dataclass
class ResolvedPackProfile:
    """The result of resolving a set of pack activations.

    Consumers (activation.py, procedure hooks, policy compilers) query this
    object rather than the raw registry.
    """

    activation_id: str
    """Unique identifier for this resolved profile (e.g. tenant_id or environment key)."""

    active_packs: list[PackManifest]
    """Packs in resolution order (highest priority first)."""

    providers: dict[PackCapability, list[Any]] = field(default_factory=dict)
    """Capability → ordered provider list across all active packs."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Arbitrary key-value context from the activation request."""

    def providers_for(self, capability: PackCapability) -> list[Any]:
        """Return all active providers for ``capability``, priority-ordered."""
        return self.providers.get(capability, [])

    def pack_ids(self) -> list[str]:
        return [m.pack_id for m in self.active_packs]

    def has_pack(self, pack_id: str) -> bool:
        return any(m.pack_id == pack_id for m in self.active_packs)


class PackResolver:
    """Resolves a pack activation request into a ResolvedPackProfile.

    Usage::

        resolver = PackResolver(registry)
        profile = resolver.resolve(
            activation_id="tenant:acme",
            requested_packs=["catenax", "battery_passport"],
        )
    """

    def __init__(self, registry: PackRegistry) -> None:
        self._registry = registry

    def resolve(
        self,
        *,
        activation_id: str,
        requested_packs: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> ResolvedPackProfile:
        """Resolve ``requested_packs`` into a ``ResolvedPackProfile``.

        Steps:
        1. Look up manifests for all requested packs.
        2. Resolve transitive dependencies (required deps only).
        3. Check for declared conflicts.
        4. Check compatibility version specs.
        5. Sort by default_priority (ascending = higher priority).
        6. Build providers dict.

        Raises:
            PackNotFoundError: If a requested or required pack is not registered.
            PackDependencyError: If a required dependency is missing or incompatible.
            PackConflictError: If two active packs declare a conflict.
            PackVersionError: If a pack's version is outside a required range.
        """
        all_ids = self._expand_dependencies(requested_packs)
        self._check_conflicts(all_ids)
        manifests = [self._registry.manifest(pid) for pid in all_ids]
        sorted_manifests = sorted(manifests, key=lambda m: m.default_priority)

        providers: dict[PackCapability, list[Any]] = {}
        for manifest in sorted_manifests:
            for cap_decl in manifest.capabilities:
                provider = self._registry.provider_for_pack(
                    manifest.pack_id, cap_decl.capability
                )
                if provider is not None:
                    providers.setdefault(cap_decl.capability, []).append(provider)

        return ResolvedPackProfile(
            activation_id=activation_id,
            active_packs=sorted_manifests,
            providers=providers,
            metadata=metadata or {},
        )

    def _expand_dependencies(self, requested: list[str]) -> list[str]:
        """BFS expansion of required pack dependencies."""
        visited: set[str] = set()
        queue = list(requested)
        while queue:
            pack_id = queue.pop(0)
            if pack_id in visited:
                continue
            visited.add(pack_id)
            manifest = self._registry.manifest(pack_id)
            for dep in manifest.dependencies:
                if not dep.required:
                    continue
                if not self._registry.has_pack(dep.pack_id):
                    raise PackDependencyError(
                        f"Pack {pack_id!r} requires {dep.pack_id!r} "
                        f"({dep.version_spec}) but it is not registered."
                    )
                dep_manifest = self._registry.manifest(dep.pack_id)
                if not versions_compatible(dep_manifest.version, dep.version_spec):
                    raise PackVersionError(
                        f"Pack {pack_id!r} requires {dep.pack_id!r} {dep.version_spec} "
                        f"but found {dep_manifest.version}."
                    )
                if dep.pack_id not in visited:
                    queue.append(dep.pack_id)
        return list(visited)

    def _check_conflicts(self, all_ids: list[str]) -> None:
        """Raise PackConflictError if any pair of active packs declares a conflict."""
        id_set = set(all_ids)
        for pack_id in all_ids:
            manifest = self._registry.manifest(pack_id)
            for conflicting in manifest.conflicts:
                if conflicting in id_set:
                    raise PackConflictError(
                        f"Pack {pack_id!r} declares a conflict with {conflicting!r}, "
                        f"but both are in the requested activation. "
                        "Remove one or declare an explicit override in a custom pack."
                    )
