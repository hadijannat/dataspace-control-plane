"""Gaia-X policy dialect provider.

Implements :class:`PolicyDialectProvider` for the ``gaiax`` dialect.

Compiles canonical policy dicts to ODRL/JSON-LD policies with the Gaia-X
namespace, and parses them back.  No external HTTP calls or persistence.

Normative reference: Gaia-X Trust Framework 22.10, §6 (Usage Policies).
"""
from __future__ import annotations

from typing import Any

from ..._shared.provenance import attach_module_provenance
from .trust_framework import GX_ODRL_CONTEXT, GX_VOCABULARY_URI

_GX_CONTEXT = [GX_ODRL_CONTEXT, {"gx": GX_VOCABULARY_URI}]

# Field mappings: canonical → ODRL/GX
_CANONICAL_TO_ODRL: dict[str, str] = {
    "action": "odrl:action",
    "target": "odrl:target",
    "assigner": "odrl:assigner",
    "assignee": "odrl:assignee",
    "constraint": "odrl:constraint",
    "purpose": "gx:purpose",
    "data_protection_regime": "gx:dataProtectionRegime",
    "access_type": "gx:accessType",
    "time_interval": "odrl:timeInterval",
}

_ODRL_TO_CANONICAL: dict[str, str] = {v: k for k, v in _CANONICAL_TO_ODRL.items()}


class GaiaXPolicyDialectProvider:
    """Compiles and parses Gaia-X ODRL/JSON-LD policies.

    Implements :class:`PolicyDialectProvider` with ``dialect_id = "gaiax"``.
    """

    dialect_id: str = "gaiax"

    # ------------------------------------------------------------------
    # PolicyDialectProvider interface
    # ------------------------------------------------------------------

    def compile(
        self,
        canonical_policy: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Compile ``canonical_policy`` to an ODRL/JSON-LD Gaia-X policy.

        Args:
            canonical_policy: Canonical policy dict from ``core/``.
            activation_scope: Tenant/scope identifier stamped on the output.

        Returns:
            ODRL/JSON-LD dict with ``@context`` and ``@type`` fields.
        """
        odrl_policy: dict[str, Any] = {
            "@context": _GX_CONTEXT,
            "@type": "odrl:Policy",
        }

        for canonical_key, value in canonical_policy.items():
            odrl_key = _CANONICAL_TO_ODRL.get(canonical_key)
            if odrl_key:
                odrl_policy[odrl_key] = value
            elif not canonical_key.startswith("_"):
                # Pass through unknown keys prefixed with gx: namespace
                odrl_policy[f"gx:{canonical_key}"] = value

        # Stamp dialect metadata (non-normative)
        odrl_policy["_gx_dialect"] = self.dialect_id
        odrl_policy["_gx_activation_scope"] = activation_scope

        return attach_module_provenance(
            odrl_policy,
            module_file=__file__,
            rule_ids=["gaia_x:policy-dialect"],
            activation_scope=activation_scope,
        )

    def parse(self, dialect_policy: dict[str, Any]) -> dict[str, Any]:
        """Parse a Gaia-X ODRL/JSON-LD policy back to a canonical policy dict.

        Args:
            dialect_policy: An ODRL/JSON-LD policy dict produced by
                            :meth:`compile`.

        Returns:
            Canonical policy dict suitable for ``core/`` processing.
        """
        canonical: dict[str, Any] = {}

        for odrl_key, value in dialect_policy.items():
            # Skip JSON-LD meta-fields and private metadata
            if odrl_key.startswith("@") or odrl_key.startswith("_"):
                continue

            canonical_key = _ODRL_TO_CANONICAL.get(odrl_key)
            if canonical_key:
                canonical[canonical_key] = value
            elif odrl_key.startswith("gx:"):
                # Strip gx: prefix for canonical representation
                canonical[odrl_key[3:]] = value
            elif odrl_key.startswith("odrl:"):
                # Strip odrl: prefix
                canonical[odrl_key[5:]] = value
            else:
                canonical[odrl_key] = value

        return attach_module_provenance(
            canonical,
            module_file=__file__,
            rule_ids=["gaia_x:policy-dialect"],
            activation_scope="parse",
        )
