"""Value objects for the twins domain."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.canonical_models.twin import AasShellRef, SubmodelRef, EndpointRef, SemanticId


@dataclass(frozen=True)
class TwinDescriptor:
    """Immutable descriptor capturing the full AAS shell reference, submodels, endpoints, and semantic IDs."""
    shell_ref: AasShellRef
    submodels: list[SubmodelRef]
    endpoints: list[EndpointRef]
    semantic_ids: list[SemanticId]


@dataclass(frozen=True)
class TwinVersion:
    """Semantic version triple with an optional label."""
    major: int
    minor: int
    patch: int
    label: str = ""

    def bump_minor(self) -> "TwinVersion":
        """Return a new TwinVersion with the minor component incremented and patch reset to 0."""
        return TwinVersion(major=self.major, minor=self.minor + 1, patch=0, label=self.label)

    def bump_major(self) -> "TwinVersion":
        """Return a new TwinVersion with the major component incremented and minor/patch reset to 0."""
        return TwinVersion(major=self.major + 1, minor=0, patch=0, label=self.label)

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.label}" if self.label else base


@dataclass(frozen=True)
class EndpointHealth:
    """Snapshot of reachability for a single endpoint URL."""
    endpoint_url: str
    is_reachable: bool
    last_checked_at: datetime | None


RegistryEntryRef = str
