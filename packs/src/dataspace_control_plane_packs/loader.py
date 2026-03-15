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
from importlib import metadata
import logging
from pathlib import Path
from typing import Any

from ._shared.capabilities import PackCapability
from ._shared.errors import PackValidationError
from ._shared.manifest import PackManifest
from ._shared.provenance import validate_manifest_sources
from .registry import PackRegistry

logger = logging.getLogger(__name__)

_PACKAGE_ROOT = Path(__file__).resolve().parent

# Ordered list of built-in pack module paths.
# Each must expose ``MANIFEST: PackManifest`` and ``PROVIDERS: dict[PackCapability, Any]``.
BUILTIN_PACKS: list[str] = [
    "dataspace_control_plane_packs.catenax.api",
    "dataspace_control_plane_packs.manufacturing_x.api",
    "dataspace_control_plane_packs.gaia_x.api",
    "dataspace_control_plane_packs.espr_dpp.api",
    "dataspace_control_plane_packs.battery_passport.api",
]

_CUSTOM_DISCOVERY_ROOTS: tuple[tuple[Path, str], ...] = (
    (
        _PACKAGE_ROOT / "custom" / "examples",
        "dataspace_control_plane_packs.custom.examples",
    ),
    (
        _PACKAGE_ROOT / "custom" / "org_packs",
        "dataspace_control_plane_packs.custom.org_packs",
    ),
)


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

    try:
        validate_manifest_sources(manifest)
    except Exception as exc:
        logger.error("Pack module %r failed normative-source validation: %s", module_path, exc)
        return False

    registry.register(manifest, providers=providers or {})
    return True


def load_all_builtin_packs(registry: PackRegistry) -> list[str]:
    """Load all built-in packs into ``registry``.

    Returns the list of successfully loaded pack IDs.
    """
    loaded: list[str] = []
    for module_path in discover_pack_modules():
        if load_pack(module_path, registry):
            # Determine the pack_id from the last registered manifest.
            for pack_id in reversed(registry.pack_ids()):
                loaded.append(pack_id)
                break
    logger.info("Loaded %d built-in packs: %s", len(loaded), loaded)
    return loaded


def discover_pack_modules() -> list[str]:
    """Return all loadable pack module paths in deterministic order."""
    discovered = list(BUILTIN_PACKS)
    seen = set(discovered)

    for module_path in _discover_inrepo_custom_modules():
        if module_path not in seen:
            discovered.append(module_path)
            seen.add(module_path)

    for module_path in _discover_entry_point_modules():
        if module_path not in seen:
            discovered.append(module_path)
            seen.add(module_path)

    return discovered


_VALID_MODULE_NAME_RE = __import__("re").compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
"""Regex for a single Python identifier component — no dots, no path separators."""

_ALLOWED_ENTRY_POINT_PREFIXES: tuple[str, ...] = (
    "dataspace_control_plane_packs.",
)
"""Entry-point module paths must begin with one of these prefixes.

This prevents third-party packages from injecting arbitrary module paths
via the ``dataspace_control_plane_packs.packs`` entry-point group.
"""


def _discover_inrepo_custom_modules() -> list[str]:
    module_paths: list[str] = []
    for root, prefix in _CUSTOM_DISCOVERY_ROOTS:
        # Resolve the root once and refuse to walk outside it.
        try:
            resolved_root = root.resolve(strict=True)
        except (OSError, RuntimeError):
            continue

        if not resolved_root.is_dir():
            continue

        for child in sorted(resolved_root.iterdir(), key=lambda path: path.name):
            # Guard 1: must be a real directory, not a symlink pointing outside.
            if child.is_symlink():
                logger.warning(
                    "Custom pack discovery: skipping symlink %s — symlinks are not allowed "
                    "in custom pack roots.",
                    child,
                )
                continue
            if not child.is_dir():
                continue

            # Guard 2: directory name must be a plain Python identifier.
            if not _VALID_MODULE_NAME_RE.match(child.name):
                logger.warning(
                    "Custom pack discovery: skipping directory %r — name is not a valid "
                    "Python identifier and cannot be used as a module name component.",
                    child.name,
                )
                continue

            # Guard 3: the child must still resolve inside the declared root
            # (defence against TOCTOU races and unusual filesystem behaviour).
            try:
                child.resolve(strict=True).relative_to(resolved_root)
            except ValueError:
                logger.warning(
                    "Custom pack discovery: skipping %s — resolved path escapes root %s.",
                    child,
                    resolved_root,
                )
                continue

            if (child / "__init__.py").is_file() and (child / "api.py").is_file():
                module_paths.append(f"{prefix}.{child.name}.api")

    return module_paths


def _discover_entry_point_modules() -> list[str]:
    try:
        entry_points = metadata.entry_points(group="dataspace_control_plane_packs.packs")
    except Exception:
        return []

    module_paths: list[str] = []
    for entry_point in sorted(entry_points, key=lambda item: item.name):
        module_path = entry_point.value
        # Guard: only accept module paths within the allowed namespace prefixes.
        if not any(module_path.startswith(pfx) for pfx in _ALLOWED_ENTRY_POINT_PREFIXES):
            logger.warning(
                "Entry-point pack %r advertises module path %r which is outside the "
                "allowed prefix list %s — skipping.",
                entry_point.name,
                module_path,
                _ALLOWED_ENTRY_POINT_PREFIXES,
            )
            continue
        module_paths.append(module_path)

    return module_paths
