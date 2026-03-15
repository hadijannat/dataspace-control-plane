"""AAS access model for DPP4.0 profiles.

Implements the access permission rule layer (AAS Part 1 §8) as it applies
to Digital Product Passports: who may read which submodel elements, and under
what policy conditions.

The access matrix is data-driven and loaded from pack-specific YAML
files — this module provides only the model and evaluation logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class AccessSubject:
    """A principal class that may access AAS content."""

    subject_class: str
    """e.g. ``public``, ``authority``, ``legitimate_interest``, ``manufacturer``."""

    description: str = ""


@dataclass(frozen=True)
class AccessPermission:
    """A permission rule for a specific subject + submodel/element path."""

    subject_class: str
    path: str
    """Dot-separated path from submodel idShort: e.g. ``Nameplate.ManufacturerName``."""
    kind: Literal["allow", "deny", "conditional"]
    condition: str | None = None
    """Free-text or URN describing the condition (e.g. ``legitimate_interest_verified``)."""
    effective_from: str | None = None
    effective_to: str | None = None


@dataclass
class AccessMatrix:
    """Collection of permissions for a DPP submodel set."""

    permissions: list[AccessPermission] = field(default_factory=list)
    version: str = "1.0"
    effective_from: str | None = None

    def may_access(
        self, subject_class: str, path: str, *, context: dict[str, Any] | None = None
    ) -> bool:
        """Return True if ``subject_class`` is allowed to access ``path``.

        Deny rules take precedence over allow rules (explicit deny wins).
        Conditional rules evaluate to False when context is absent.
        """
        for perm in self.permissions:
            if perm.subject_class != subject_class:
                continue
            if not _path_matches(perm.path, path):
                continue
            if perm.kind == "deny":
                return False
            if perm.kind == "allow":
                return True
            if perm.kind == "conditional":
                if context is None:
                    return False
                return bool(context.get(perm.condition, False))
        return False  # default deny

    @classmethod
    def from_dicts(cls, records: list[dict[str, Any]], *, version: str = "1.0") -> "AccessMatrix":
        """Build an AccessMatrix from a list of plain dicts (e.g. from YAML load)."""
        perms = [
            AccessPermission(
                subject_class=r["subject_class"],
                path=r["path"],
                kind=r["kind"],
                condition=r.get("condition"),
                effective_from=r.get("effective_from"),
                effective_to=r.get("effective_to"),
            )
            for r in records
        ]
        return cls(permissions=perms, version=version)


def _path_matches(pattern: str, path: str) -> bool:
    """Match a permission path pattern against a concrete path.

    Supports ``*`` as a wildcard for any single segment and ``**`` for any subtree.
    """
    if pattern == "**":
        return True
    if "*" not in pattern:
        return pattern == path or path.startswith(pattern + ".")
    parts_p = pattern.split(".")
    parts_c = path.split(".")
    return _match_parts(parts_p, parts_c)


def _match_parts(pattern: list[str], concrete: list[str]) -> bool:
    if not pattern:
        return not concrete
    if pattern[0] == "**":
        return True
    if pattern[0] == "*":
        if not concrete:
            return False
        return _match_parts(pattern[1:], concrete[1:])
    if not concrete or pattern[0] != concrete[0]:
        return False
    return _match_parts(pattern[1:], concrete[1:])
