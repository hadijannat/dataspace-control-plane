"""Pack loader — discovers and imports concrete packs, populates the registry.

Discovery strategy:
1. Built-in packs (subpackages of ``dataspace_control_plane_packs``) are
   registered explicitly in ``BUILTIN_PACKS``.
2. Each built-in pack must expose ``api.MANIFEST`` and ``api.PROVIDERS``.
3. Third-party packs may register via entry-points (future extension).

Call ``load_all_builtin_packs(registry)`` at application startup.
"""
from __future__ import annotations

import importlib
import logging
from typing import Any

from ._shared.capabilities import PackCapability
from ._shared.errors import PackValidationError
from ._shared.manifest import PackManifest
from .registry import PackRegistry

logger = logging.getLogger(__name__)

# Ordered list of built-in pack module paths.
# Each must expose ``MANIFEST: PackManifest`` and ``PROVIDERS: dict[PackCapability, Any]``.
BUILTIN_PACKS: list[str] = [
    "dataspace_control_plane_packs.catenax.api",
    "dataspace_control_plane_packs.manufacturing_x.api",
    "dataspace_control_plane_packs.gaia_x.api",
    "dataspace_control_plane_packs.espr_dpp.api",
    "dataspace_control_plane_packs.battery_passport.api",
]


def load_pack(module_path: str, registry: PackRegistry) -> bool:
    """Import a pack module and register it into ``registry``.

    Returns True on success, False on error (logs the error).
    """
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        logger.error("Cannot import pack module %r: %s", module_path, exc)
        return False

    manifest: PackManifest | None = getattr(module, "MANIFEST", None)
    providers: dict[PackCapability, Any] | None = getattr(module, "PROVIDERS", None)

    if manifest is None:
        logger.error(
            "Pack module %r does not expose a MANIFEST attribute. "
            "Add ``MANIFEST: PackManifest = ...`` to its api.py.",
            module_path,
        )
        return False

    registry.register(manifest, providers=providers or {})
    return True


def load_all_builtin_packs(registry: PackRegistry) -> list[str]:
    """Load all built-in packs into ``registry``.

    Returns the list of successfully loaded pack IDs.
    """
    loaded: list[str] = []
    for module_path in BUILTIN_PACKS:
        if load_pack(module_path, registry):
            # Determine the pack_id from the last registered manifest.
            for pack_id in reversed(registry.pack_ids()):
                loaded.append(pack_id)
                break
    logger.info("Loaded %d built-in packs: %s", len(loaded), loaded)
    return loaded
