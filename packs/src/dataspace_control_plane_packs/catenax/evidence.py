"""Catena-X evidence augmenter.

Adds Catena-X-specific fields to evidence bundles so that audit trails
carry BPN identity, governance acceptance, and policy purpose references
in a standardised namespace.
"""
from __future__ import annotations

from typing import Any

from .._shared.provenance import attach_module_provenance

_PACK_VERSION = "4.0.0"
_EVIDENCE_RULE_IDS = [
    "catenax:bpnl-required",
    "catenax:deg-acceptance-required",
    "catenax:connector-registration-required",
    "catenax:policy-profile",
]


class CatenaxEvidenceAugmenter:
    """EvidenceAugmenter that injects Catena-X fields into evidence dicts."""

    def augment(
        self,
        evidence: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Add Catena-X-specific fields to ``evidence``.

        Existing fields are never removed. Added fields are namespaced under
        the ``cx:`` prefix to avoid collisions with core evidence fields.

        Fields added:
          - ``cx:bpnl`` — from ``evidence["bpnl"]`` or ``evidence["legal_entity_id"]``
          - ``cx:governance_acceptance_ref`` — from ``evidence["governance_acceptance_ref"]``
          - ``cx:connector_registration_ref`` — from ``evidence["connector_registration_ref"]``
          - ``cx:policy_purpose_refs`` — from ``evidence["policy_purposes"]``
          - ``cx:pack_version`` — always ``"4.0.0"``
        """
        augmented = dict(evidence)

        bpnl = evidence.get("bpnl", "") or evidence.get("legal_entity_id", "")
        augmented["cx:bpnl"] = bpnl

        governance_ref = evidence.get("governance_acceptance_ref")
        if governance_ref is not None:
            augmented["cx:governance_acceptance_ref"] = governance_ref

        connector_ref = evidence.get("connector_registration_ref")
        if connector_ref is not None:
            augmented["cx:connector_registration_ref"] = connector_ref

        policy_purposes = evidence.get("policy_purposes", [])
        augmented["cx:policy_purpose_refs"] = list(policy_purposes)

        augmented["cx:pack_version"] = _PACK_VERSION

        return attach_module_provenance(
            augmented,
            module_file=__file__,
            rule_ids=_EVIDENCE_RULE_IDS,
            activation_scope=activation_scope,
        )
