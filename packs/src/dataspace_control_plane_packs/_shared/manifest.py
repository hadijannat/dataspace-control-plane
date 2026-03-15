"""PackManifest — the declaration a pack makes about itself.

Manifests are frozen dataclasses so they can safely serve as dict keys and
appear in sets. They are parsed from ``manifest.toml`` at pack load time.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .capabilities import PackCapability
from .errors import PackValidationError
from .provenance import NormativeSource


@dataclass(frozen=True)
class PackCapabilityDecl:
    """Declaration that a pack implements a specific capability interface.

    ``interface_class`` is the fully qualified name of the Python object in
    ``api.py`` that provides the capability.
    """

    capability: PackCapability
    interface_class: str


@dataclass(frozen=True)
class PackDependency:
    """A required or optional dependency on another pack."""

    pack_id: str
    version_spec: str
    """Semver-style version specifier (e.g. ``>=1.0.0``, ``^2.3.0``)."""
    required: bool = True


@dataclass(frozen=True)
class PackManifest:
    """Complete declaration of a pack's identity, dependencies, and capabilities.

    Parsed from each pack's ``manifest.toml``. Immutable after load.
    """

    pack_id: str
    """Globally unique pack identifier (e.g. ``catenax``, ``battery_passport``)."""

    pack_kind: Literal["ecosystem", "regulation", "custom"]
    """High-level classification of the pack."""

    version: str
    """SemVer version string."""

    display_name: str
    description: str

    compatibility: dict[str, str]
    """Compatibility constraints on adjacent layers (e.g. ``{"core": ">=0.1.0"}``)."""

    activation_scope: Literal["tenant", "legal_entity", "environment"]
    """Granularity at which this pack is activated."""

    dependencies: tuple[PackDependency, ...]
    conflicts: tuple[str, ...]
    """pack_ids this pack is incompatible with."""

    capabilities: tuple[PackCapabilityDecl, ...]
    normative_sources: tuple[NormativeSource, ...]
    default_priority: int
    """Lower number = higher priority in reducers. Default 100."""
    root_dir: str = field(repr=False, compare=False, hash=False, default=".")
    """Filesystem directory that owns this manifest and its pinned assets."""

    @classmethod
    def from_toml(cls, path: Path) -> "PackManifest":
        """Load a PackManifest from a ``manifest.toml`` file.

        Raises:
            PackValidationError: If required fields are missing or malformed.
        """
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception as exc:
            raise PackValidationError(f"Cannot load manifest {path}: {exc}") from exc

        try:
            deps = tuple(
                PackDependency(
                    pack_id=d["pack_id"],
                    version_spec=d.get("version_spec", "*"),
                    required=d.get("required", True),
                )
                for d in data.get("dependencies", [])
            )
            caps = tuple(
                PackCapabilityDecl(
                    capability=PackCapability(c["capability"]),
                    interface_class=c["interface_class"],
                )
                for c in data.get("capabilities", [])
            )
            sources = tuple(
                NormativeSource(
                    source_uri=s["source_uri"],
                    version=s["version"],
                    retrieval_date=s["retrieval_date"],
                    sha256=s["sha256"],
                    local_filename=s["local_filename"],
                    effective_from=s.get("effective_from"),
                    effective_to=s.get("effective_to"),
                    upstream_license=s.get("upstream_license"),
                )
                for s in data.get("normative_sources", [])
            )
            return cls(
                pack_id=data["pack_id"],
                pack_kind=data["pack_kind"],
                version=data["version"],
                display_name=data["display_name"],
                description=data["description"],
                compatibility=data.get("compatibility", {}),
                activation_scope=data.get("activation_scope", "tenant"),
                dependencies=deps,
                conflicts=tuple(data.get("conflicts", [])),
                capabilities=caps,
                normative_sources=sources,
                default_priority=data.get("default_priority", 100),
                root_dir=str(path.parent),
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise PackValidationError(
                f"Malformed manifest in {path}: {exc}"
            ) from exc


def _minimal_manifest(
    pack_id: str,
    pack_kind: Literal["ecosystem", "regulation", "custom"],
    version: str,
    display_name: str,
    description: str,
    capabilities: list[PackCapabilityDecl] | None = None,
) -> PackManifest:
    """Build a minimal in-memory manifest without a TOML file (for testing)."""
    return PackManifest(
        pack_id=pack_id,
        pack_kind=pack_kind,
        version=version,
        display_name=display_name,
        description=description,
        compatibility={},
        activation_scope="tenant",
        dependencies=(),
        conflicts=(),
        capabilities=tuple(capabilities or []),
        normative_sources=(),
        default_priority=100,
        root_dir=".",
    )
