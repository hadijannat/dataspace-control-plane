"""Pack registry — stores manifests and capability providers.

The registry is the authoritative in-process store of which packs are
registered and which capabilities they provide. It is populated by
``loader.py`` at application startup.

Thread safety: the registry is populated once at startup and read-only
during request processing. No locks required for reads.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, TypeVar

from ._shared.capabilities import PackCapability
from ._shared.errors import PackNotFoundError
from ._shared.manifest import PackManifest

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PackRegistry:
    """Central registry of registered packs and their capability providers.

    Usage::

        registry = PackRegistry()
        registry.register(manifest, providers={"RequirementProvider": my_provider})
        providers = registry.providers_for(PackCapability.REQUIREMENT_PROVIDER)
    """

    def __init__(self) -> None:
        self._manifests: dict[str, PackManifest] = {}
        self._providers: dict[PackCapability, list[Any]] = defaultdict(list)
        self._raw_providers: dict[str, dict[PackCapability, Any]] = {}

    def register(
        self,
        manifest: PackManifest,
        *,
        providers: dict[PackCapability, Any] | None = None,
    ) -> None:
        """Register a pack manifest and its capability provider instances.

        Args:
            manifest: The pack's manifest.
            providers: Map from PackCapability → provider instance. Only
                capabilities declared in manifest.capabilities should be included.
        """
        if manifest.pack_id in self._manifests:
            logger.warning("Pack %r already registered; overwriting.", manifest.pack_id)

        self._manifests[manifest.pack_id] = manifest
        providers = providers or {}
        self._raw_providers[manifest.pack_id] = {}

        for cap_decl in manifest.capabilities:
            provider = providers.get(cap_decl.capability)
            if provider is not None:
                self._providers[cap_decl.capability].append(provider)
                self._raw_providers[manifest.pack_id][cap_decl.capability] = provider
            else:
                logger.debug(
                    "Pack %r declares capability %s but no provider instance was given.",
                    manifest.pack_id,
                    cap_decl.capability,
                )

        logger.info("Registered pack %r v%s", manifest.pack_id, manifest.version)

    def manifests(self) -> list[PackManifest]:
        """Return all registered pack manifests."""
        return list(self._manifests.values())

    def manifest(self, pack_id: str) -> PackManifest:
        """Return the manifest for ``pack_id``.

        Raises:
            PackNotFoundError: If the pack is not registered.
        """
        try:
            return self._manifests[pack_id]
        except KeyError:
            raise PackNotFoundError(f"Pack {pack_id!r} is not registered.")

    def providers_for(self, capability: PackCapability) -> list[Any]:
        """Return all provider instances for the given capability, in registration order."""
        return list(self._providers.get(capability, []))

    def pack_ids(self) -> list[str]:
        """Return all registered pack IDs."""
        return list(self._manifests.keys())

    def has_pack(self, pack_id: str) -> bool:
        return pack_id in self._manifests

    def provider_for_pack(
        self, pack_id: str, capability: PackCapability
    ) -> Any | None:
        """Return the capability provider for a specific pack, or None."""
        return self._raw_providers.get(pack_id, {}).get(capability)


# Module-level singleton registry.
# Application code should call ``get_registry()`` rather than importing
# this directly, so tests can inject a fresh registry.
_GLOBAL_REGISTRY: PackRegistry | None = None


def get_registry() -> PackRegistry:
    """Return the global pack registry, creating it on first access."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = PackRegistry()
    return _GLOBAL_REGISTRY


def reset_registry() -> None:
    """Reset the global registry (for tests only)."""
    global _GLOBAL_REGISTRY
    _GLOBAL_REGISTRY = None
