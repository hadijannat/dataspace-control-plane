"""Version primitives for aggregates, pack requirements, and procedure schemas."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionTag:
    """Semantic version: ``major.minor.patch``."""

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        if any(v < 0 for v in (self.major, self.minor, self.patch)):
            raise ValueError("VersionTag components must be non-negative")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "VersionTag") -> bool:
        return self.major == other.major

    @classmethod
    def parse(cls, raw: str) -> "VersionTag":
        parts = raw.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version tag: {raw!r}")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))


CURRENT_KERNEL_VERSION = VersionTag(1, 0, 0)
