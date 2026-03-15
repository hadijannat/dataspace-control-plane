"""Compiler for Catena-X ODRL policies.

Compiles canonical policy dicts into Catena-X ODRL dialect representation
and delegates parsing back to the parser module.

All cx-policy:* vocabulary stays inside this package.
"""
from __future__ import annotations

from typing import Any

from .parser import parse_cx_policy
from .purposes_loader import load_purposes

_CX_ODRL_CONTEXT = [
    "https://www.w3.org/ns/odrl.jsonld",
    {"cx-policy": "https://w3id.org/catenax/policy/"},
]

_CX_USAGE_PURPOSE_LEFT_OPERAND = "cx-policy:UsagePurpose"


def _build_purpose_index() -> dict[str, dict[str, Any]]:
    """Build a dict mapping purpose ID to its full definition from purposes.yaml."""
    data = load_purposes()
    return {p["id"]: p for p in data.get("purposes", [])}


class CatenaxPolicyDialectProvider:
    """PolicyDialectProvider for the Catena-X ODRL profile (version 24.05)."""

    dialect_id: str = "catenax"

    def compile(
        self,
        canonical_policy: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Compile a canonical policy into a Catena-X ODRL dict.

        Produces:
          - ``@context`` with the standard ODRL and cx-policy prefixes
          - ``@type`` as ``"odrl:Offer"`` or ``"odrl:Agreement"``
          - ``odrl:permission`` built from ``canonical_policy["permissions"]``
          - Purposes mapped via the purposes.yaml vocabulary
        """
        purpose_index = _build_purpose_index()

        policy_type = (
            "odrl:Agreement"
            if canonical_policy.get("type") == "agreement"
            else "odrl:Offer"
        )

        permissions = _compile_permissions(
            canonical_policy.get("permissions", []),
            purpose_index,
        )
        prohibitions = _compile_rules(canonical_policy.get("prohibitions", []))
        obligations = _compile_rules(canonical_policy.get("obligations", []))

        result: dict[str, Any] = {
            "@context": _CX_ODRL_CONTEXT,
            "@type": policy_type,
            "odrl:permission": permissions,
        }
        if prohibitions:
            result["odrl:prohibition"] = prohibitions
        if obligations:
            result["odrl:obligation"] = obligations
        if canonical_policy.get("uid"):
            result["@id"] = canonical_policy["uid"]

        return result

    def parse(self, dialect_policy: dict[str, Any]) -> dict[str, Any]:
        """Parse a Catena-X ODRL policy dict back to a canonical policy dict."""
        return parse_cx_policy(dialect_policy)


def _compile_permissions(
    permissions: list[dict[str, Any]],
    purpose_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compile canonical permissions, injecting cx-policy purpose constraints."""
    compiled: list[dict[str, Any]] = []
    for perm in permissions:
        cx_perm: dict[str, Any] = {}

        if "action" in perm:
            cx_perm["odrl:action"] = perm["action"]
        if "target" in perm:
            cx_perm["odrl:target"] = perm["target"]

        constraints: list[dict[str, Any]] = []

        for purpose_id in perm.get("purposes", []):
            resolved = purpose_index.get(purpose_id)
            if resolved:
                constraints.append(
                    {
                        "odrl:leftOperand": _CX_USAGE_PURPOSE_LEFT_OPERAND,
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": purpose_id,
                    }
                )
            else:
                constraints.append(
                    {
                        "odrl:leftOperand": _CX_USAGE_PURPOSE_LEFT_OPERAND,
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": purpose_id,
                    }
                )

        for raw_constraint in perm.get("odrl:constraint", []):
            constraints.append(raw_constraint)

        if constraints:
            cx_perm["odrl:constraint"] = constraints

        for key, value in perm.items():
            if key not in ("action", "target", "purposes", "odrl:constraint"):
                cx_perm[key] = value

        compiled.append(cx_perm)

    return compiled


def _compile_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pass-through compilation for prohibitions and obligations."""
    return list(rules)
