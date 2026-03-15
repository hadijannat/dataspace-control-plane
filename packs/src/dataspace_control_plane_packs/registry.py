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
from ._shared.errors import PackNotFoundError, PackValidationError
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
        self._raw_providers: dict[str, dict[PackCapability, tuple[Any, ...]]] = {}

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

        declared_capabilities = {cap_decl.capability for cap_decl in manifest.capabilities}
        normalized_inputs: dict[PackCapability, tuple[Any, ...]] = {}
        for raw_capability, raw_provider in providers.items():
            capability = (
                raw_capability
                if isinstance(raw_capability, PackCapability)
                else PackCapability(raw_capability)
            )
            if capability not in declared_capabilities:
                raise PackValidationError(
                    f"Pack {manifest.pack_id!r} registers provider(s) for {capability.value!r} "
                    "without declaring that capability in manifest.toml."
                )
            normalized_inputs[capability] = self._normalize_providers(raw_provider)

        for capability in declared_capabilities:
            provider_instances = normalized_inputs.get(capability, ())
            if provider_instances:
                self._providers[capability].extend(provider_instances)
                self._raw_providers[manifest.pack_id][capability] = provider_instances
            else:
                logger.debug(
                    "Pack %r declares capability %s but no provider instance was given.",
                    manifest.pack_id,
                    capability,
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
        providers = self._raw_providers.get(pack_id, {}).get(capability, ())
        return providers[0] if providers else None

    def providers_for_pack(
        self, pack_id: str, capability: PackCapability
    ) -> list[Any]:
        """Return all capability providers registered for a specific pack."""
        return list(self._raw_providers.get(pack_id, {}).get(capability, ()))

    @staticmethod
    def _normalize_providers(raw_provider: Any) -> tuple[Any, ...]:
        if raw_provider is None:
            return ()
        if isinstance(raw_provider, (list, tuple)):
            return tuple(item for item in raw_provider if item is not None)
        return (raw_provider,)


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
