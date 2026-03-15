"""Enterprise policy overlay — example implementation.

This module demonstrates the ``EvidenceAugmenter`` capability for an enterprise
that layers additional internal controls on top of the Catena-X pack.

INVARIANT — stricter only, never weaker:
  This overlay adds new evidence fields required by the enterprise's internal
  audit policy. It does not touch existing fields and does not weaken any
  active regulatory rule. The ``check_override_safety`` function from
  ``_shared.reducers`` is the enforcement mechanism for this invariant when
  custom rules target the same ``rule_id`` as a regulatory rule.

This is an EXAMPLE pack. It is not for production use. Copy to
``custom/org_packs/<your_org_id>/`` and update the manifest before activating
in a real deployment.
"""
from __future__ import annotations

from typing import Any

from ...._shared.manifest import PackManifest, PackCapabilityDecl, _minimal_manifest
from ...._shared.capabilities import PackCapability
from ...._shared.reducers import check_override_safety  # noqa: F401 — re-exported for transparency
from ...._shared.rule_model import RuleDefinition

# ---------------------------------------------------------------------------
# Data classification levels (internal vocabulary — not canonical)
# ---------------------------------------------------------------------------

_DATA_CLASSIFICATIONS = ("public", "internal", "confidential", "restricted")
_DEFAULT_CLASSIFICATION = "internal"

# ---------------------------------------------------------------------------
# EvidenceAugmenter
# ---------------------------------------------------------------------------

class EnterpriseEvidenceAugmenter:
    """EvidenceAugmenter that injects enterprise-specific audit fields.

    Fields added (all namespaced under ``enterprise:``):
      - ``enterprise:audit_required``      — always ``True``; flags this evidence
        bundle for enterprise audit pipeline ingestion.
      - ``enterprise:data_classification`` — data sensitivity level derived from
        ``evidence["data_classification"]``, defaulting to ``"internal"``.
      - ``enterprise:retention_policy``    — retention period derived from
        ``evidence["retention_policy"]``, defaulting to ``"7y"`` (7 years).

    INVARIANT:
      This augmenter only ADDS fields. It never removes or replaces fields set
      by preceding augmenters (e.g. the Catena-X augmenter's ``cx:`` namespace).
      The reducer in ``_shared/reducers.reduce_evidence`` enforces this at the
      framework level, but this implementation is written defensively to make
      the contract explicit.

    Override safety:
      If this overlay also registers custom ``RuleDefinition`` objects that share
      a ``rule_id`` with a regulatory pack, use ``check_override_safety`` before
      returning those rules:

        from dataspace_control_plane_packs._shared.reducers import check_override_safety
        violations = check_override_safety(
            custom_rules=my_rules,
            regulatory_rules=active_regulatory_rules,
        )
        if violations:
            raise ValueError(violations)
    """

    def augment(
        self,
        evidence: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Add enterprise audit fields to ``evidence``.

        Args:
            evidence: Existing evidence dict (may already carry ``cx:`` fields
                from a preceding Catena-X augmenter).
            activation_scope: Tenant or legal-entity identifier for provenance
                stamping.

        Returns:
            A new dict containing all original fields plus the enterprise
            additions. No existing fields are removed or modified.
        """
        augmented = dict(evidence)

        # Always require enterprise audit processing for this activation scope.
        augmented["enterprise:audit_required"] = True

        # Classify data sensitivity. Accept caller-supplied value if it is a
        # known level; otherwise fall back to the safe default.
        supplied_classification = evidence.get("data_classification")
        if supplied_classification in _DATA_CLASSIFICATIONS:
            augmented["enterprise:data_classification"] = supplied_classification
        else:
            augmented["enterprise:data_classification"] = _DEFAULT_CLASSIFICATION

        # Retention period. Accept caller-supplied value; default to 7 years
        # as required by the enterprise data governance policy.
        retention = evidence.get("retention_policy", "7y")
        augmented["enterprise:retention_policy"] = retention

        return augmented


# ---------------------------------------------------------------------------
# Pack manifest and provider registry
# ---------------------------------------------------------------------------

MANIFEST: PackManifest = _minimal_manifest(
    pack_id="example_enterprise_policy_overlay",
    pack_kind="custom",
    version="1.0.0",
    display_name="Example Enterprise Policy Overlay",
    description=(
        "Reference example of an enterprise evidence overlay. "
        "Adds stricter internal audit fields on top of the Catena-X pack. "
        "Not for production use."
    ),
    capabilities=[
        PackCapabilityDecl(
            capability=PackCapability.EVIDENCE_AUGMENTER,
            interface_class=(
                "dataspace_control_plane_packs.custom.examples"
                ".enterprise_policy_overlay.api.EnterpriseEvidenceAugmenter"
            ),
        )
    ],
)

PROVIDERS: dict[PackCapability, Any] = {
    PackCapability.EVIDENCE_AUGMENTER: EnterpriseEvidenceAugmenter(),
}
