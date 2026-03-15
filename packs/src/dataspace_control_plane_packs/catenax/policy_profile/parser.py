"""Parser for Catena-X ODRL policies.

Reads dialect-specific Catena-X ODRL policy dicts and extracts
canonical fields for use within the packs layer.

All cx-policy:* vocabulary stays inside this package and is never
leaked to core/ or other layers.
"""
from __future__ import annotations

from typing import Any

_CX_POLICY_PREFIX = "cx-policy:"


def parse_cx_policy(dialect_policy: dict[str, Any]) -> dict[str, Any]:
    """Extract canonical fields from a Catena-X ODRL policy dict.

    Reads ``odrl:permission[].odrl:constraint`` entries looking for
    ``cx-policy:*`` terms. Returns a canonical dict with:
      - ``permissions``: list of permission dicts
      - ``prohibitions``: list of prohibition dicts
      - ``obligations``: list of obligation dicts
      - ``purposes``: list of extracted purpose IDs from cx-policy constraints

    Falls back to returning raw constraints if no cx-policy terms are found.
    """
    permissions = _normalise_list(dialect_policy.get("odrl:permission", []))
    prohibitions = _normalise_list(dialect_policy.get("odrl:prohibition", []))
    obligations = _normalise_list(dialect_policy.get("odrl:obligation", []))

    purposes: list[str] = []
    canonical_permissions: list[dict[str, Any]] = []

    for perm in permissions:
        constraints = _normalise_list(perm.get("odrl:constraint", []))
        cx_purposes, other_constraints = _split_cx_constraints(constraints)
        purposes.extend(cx_purposes)

        canonical_perm: dict[str, Any] = {k: v for k, v in perm.items() if k != "odrl:constraint"}
        if other_constraints:
            canonical_perm["odrl:constraint"] = other_constraints
        if cx_purposes:
            canonical_perm["cx_purposes"] = cx_purposes
        canonical_permissions.append(canonical_perm)

    return {
        "permissions": canonical_permissions,
        "prohibitions": prohibitions,
        "obligations": obligations,
        "purposes": purposes,
    }


def _normalise_list(value: Any) -> list[Any]:
    """Coerce a value that may be a single item or a list into a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _split_cx_constraints(
    constraints: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Split constraints into cx-policy purpose IDs and all others.

    Returns:
        A tuple of (purpose_ids, remaining_constraints).
    """
    purposes: list[str] = []
    remaining: list[dict[str, Any]] = []

    for constraint in constraints:
        left_operand = constraint.get("odrl:leftOperand", "")
        right_operand = constraint.get("odrl:rightOperand", "")

        if isinstance(left_operand, str) and left_operand.startswith(_CX_POLICY_PREFIX):
            if isinstance(right_operand, str):
                purposes.append(right_operand)
            else:
                remaining.append(constraint)
        else:
            remaining.append(constraint)

    return purposes, remaining
