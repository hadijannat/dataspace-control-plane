"""
VersionTag: semantic versioning for aggregate schemas, pack rules, and policy sets.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class VersionTag:
    """Semantic version: major.minor.patch."""
    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        if any(v < 0 for v in (self.major, self.minor, self.patch)):
            raise ValueError("VersionTag components must be non-negative")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "VersionTag") -> bool:
        """Returns True if this version is backward-compatible with `other` (same major)."""
        return self.major == other.major

    @classmethod
    def parse(cls, s: str) -> "VersionTag":
        parts = s.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version tag: {s!r}")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))
