"""Semantic version utilities for pack compatibility checking.

Uses PEP 440-style version specifiers for compatibility ranges stored in
PackManifest.compatibility. Comparison delegates to semver for packs and
to packaging.version for Python-style ranges on runtime APIs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    pre: str | None = None

    @classmethod
    def parse(cls, s: str) -> "SemVer":
        """Parse a semantic version string.

        Raises:
            ValueError: If the string is not a valid SemVer.
        """
        m = _SEMVER_RE.match(s.strip())
        if not m:
            raise ValueError(f"Not a valid SemVer: {s!r}")
        return cls(
            major=int(m.group("major")),
            minor=int(m.group("minor")),
            patch=int(m.group("patch")),
            pre=m.group("pre"),
        )

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.pre}" if self.pre else base

    def _tuple(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __lt__(self, other: "SemVer") -> bool:
        return self._tuple() < other._tuple()

    def __le__(self, other: "SemVer") -> bool:
        return self._tuple() <= other._tuple()

    def __gt__(self, other: "SemVer") -> bool:
        return self._tuple() > other._tuple()

    def __ge__(self, other: "SemVer") -> bool:
        return self._tuple() >= other._tuple()

    def is_compatible_with(self, spec: str) -> bool:
        """Return True if this version satisfies the specifier string.

        Supported specifier forms:
          ``>=x.y.z``  — at least this version
          ``>=x.y.z,<a.b.c``  — range (AND)
          ``^x.y.z``   — compatible release (same major, >= minor.patch)
          ``~x.y.z``   — patch-compatible (same major.minor, >= patch)
          ``*``        — any version
        """
        spec = spec.strip()
        if spec == "*":
            return True
        if spec.startswith("^"):
            floor = SemVer.parse(spec[1:])
            return self.major == floor.major and self >= floor
        if spec.startswith("~"):
            floor = SemVer.parse(spec[1:])
            return self.major == floor.major and self.minor == floor.minor and self >= floor
        parts = [p.strip() for p in spec.split(",")]
        for part in parts:
            if part.startswith(">="):
                if not (self >= SemVer.parse(part[2:])):
                    return False
            elif part.startswith(">"):
                if not (self > SemVer.parse(part[1:])):
                    return False
            elif part.startswith("<="):
                if not (self <= SemVer.parse(part[2:])):
                    return False
            elif part.startswith("<"):
                if not (self < SemVer.parse(part[1:])):
                    return False
            elif part.startswith("=="):
                if not (self == SemVer.parse(part[2:])):
                    return False
        return True


def versions_compatible(pack_version: str, spec: str) -> bool:
    """Top-level helper: parse pack_version and check against spec string."""
    return SemVer.parse(pack_version).is_compatible_with(spec)
