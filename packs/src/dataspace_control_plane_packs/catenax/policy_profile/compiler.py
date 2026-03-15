"""Compiler for Catena-X ODRL policies.

Compiles canonical policy dicts into Catena-X ODRL dialect representation
and delegates parsing back to the parser module.

All cx-policy:* vocabulary stays inside this package.
"""
from __future__ import annotations

from typing import Any

from ..._shared.provenance import attach_module_provenance
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
        review_flags = _collect_review_flags(canonical_policy)

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
        if review_flags:
            result["review_flags"] = review_flags

        return attach_module_provenance(
            result,
            module_file=__file__,
            rule_ids=["catenax:policy-profile", "catenax:policy-purpose-catalog"],
            activation_scope=activation_scope,
        )

    def parse(self, dialect_policy: dict[str, Any]) -> dict[str, Any]:
        """Parse a Catena-X ODRL policy dict back to a canonical policy dict."""
        return parse_cx_policy(dialect_policy)


_CANONICAL_PERMISSION_KEYS = frozenset({
    "action",
    "target",
    "purposes",
    "odrl:constraint",
    "unsupported_constraints",
    "cx_purposes",
    "review_flags",
})
"""Keys on a canonical permission dict that this compiler knows how to handle.

Any other key is treated as unknown and is dropped with a warning rather than
being passed into the compiled output.  This prevents crafted input dicts from
injecting arbitrary ODRL keys into the compiled policy.
"""

import logging as _logging
_compiler_logger = _logging.getLogger(__name__)


def _compile_permissions(
    permissions: list[dict[str, Any]],
    purpose_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compile canonical permissions, injecting cx-policy purpose constraints.

    Security: Only known canonical permission keys are mapped to the output.
    Unknown keys are dropped and a warning is emitted.  This prevents caller-
    controlled data from injecting arbitrary ODRL keys (policy injection).

    Unsupported constraints (collected by the parser for manual review) are
    intentionally excluded from the compiled output; they should not be
    forwarded to downstream ODRL evaluators because their semantics are unknown.
    """
    compiled: list[dict[str, Any]] = []
    for perm in permissions:
        cx_perm: dict[str, Any] = {}

        if "action" in perm:
            cx_perm["odrl:action"] = perm["action"]
        if "target" in perm:
            cx_perm["odrl:target"] = perm["target"]

        constraints: list[dict[str, Any]] = []

        for purpose_id in perm.get("purposes", []):
            if not isinstance(purpose_id, str):
                _compiler_logger.warning(
                    "Skipping non-string purpose_id %r in cx policy compilation.", purpose_id
                )
                continue
            # Emit the purpose constraint only when the purpose is in the
            # known-good purpose catalog.  Unknown purpose IDs are not emitted
            # so that arbitrary strings cannot be injected as ODRL right operands.
            if purpose_id in purpose_index:
                constraints.append(
                    {
                        "odrl:leftOperand": _CX_USAGE_PURPOSE_LEFT_OPERAND,
                        "odrl:operator": {"@id": "odrl:eq"},
                        "odrl:rightOperand": purpose_id,
                    }
                )
            else:
                _compiler_logger.warning(
                    "Catena-X policy compiler: purpose_id %r is not in the purpose catalog "
                    "and will not be emitted in the compiled output.",
                    purpose_id,
                )

        # Pass through only already-parsed, non-cx ODRL constraints.
        # Do NOT forward unsupported_constraints — those have unknown semantics
        # and must not be emitted into valid ODRL payloads.
        for raw_constraint in perm.get("odrl:constraint", []):
            constraints.append(raw_constraint)

        if constraints:
            cx_perm["odrl:constraint"] = constraints

        # Explicitly drop unknown keys rather than using a catch-all copy.
        unknown_keys = set(perm.keys()) - _CANONICAL_PERMISSION_KEYS
        if unknown_keys:
            _compiler_logger.warning(
                "Catena-X policy compiler: dropping unknown permission keys %s — "
                "only declared canonical keys are forwarded to compiled output.",
                sorted(unknown_keys),
            )

        compiled.append(cx_perm)

    return compiled


def _compile_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pass-through compilation for prohibitions and obligations."""
    return list(rules)


def _collect_review_flags(canonical_policy: dict[str, Any]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    for permission in canonical_policy.get("permissions", []):
        flags.extend(permission.get("review_flags", []))
        if permission.get("unsupported_constraints"):
            flags.append(
                {
                    "code": "unsupported_cx_constraint",
                    "message": "Unsupported Catena-X constraints were preserved in odrl:constraint.",
                }
            )
    flags.extend(canonical_policy.get("review_flags", []))
    return flags
