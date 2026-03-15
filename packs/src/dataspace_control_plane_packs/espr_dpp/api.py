"""Public API surface for the ESPR DPP regulation pack.

Exposes the pack manifest, capability providers, and all public classes.
The registry resolves this pack by the ``MANIFEST`` and ``PROVIDERS``
attributes; all concrete classes are also exported for direct import.

Reference: Regulation (EU) 2024/1781 (ESPR)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .._shared.capabilities import PackCapability
from .._shared.manifest import PackManifest
from .._shared.provenance import attach_module_provenance
from .core_rules.evidence import EsprEvidenceAugmenter
from .implementation_profiles.aas_dpp4o.dpp_submodels import build_espr_dpp_submodel
from .requirements import EsprRequirementProvider

# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

MANIFEST = PackManifest.from_toml(Path(__file__).parent / "manifest.toml")
_TEMPLATE_RULE_IDS = [
    "espr_dpp:identifier-obligation",
    "espr_dpp:data-carrier-obligation",
    "espr_dpp:registry-obligation",
    "espr_dpp:backup-copy-obligation",
    "espr_dpp:accessibility-obligation",
]


# ---------------------------------------------------------------------------
# TwinTemplateProvider
# ---------------------------------------------------------------------------


class EsprAasTwinTemplateProvider:
    """TwinTemplateProvider for ESPR DPP AAS submodel templates."""

    def templates(self, *, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Return ESPR DPP twin template descriptors."""
        templates = [
            {
                "template_id": "espr_dpp_v1",
                "submodel": "espr_dpp",
                "regulation": "EU 2024/1781",
                "description": (
                    "ESPR Digital Product Passport AAS submodel template (v1). "
                    "Covers core DPP obligations: identifier, carrier, registry, "
                    "backup, and accessibility."
                ),
            }
        ]
        return [
            attach_module_provenance(
                template,
                module_file=__file__,
                rule_ids=_TEMPLATE_RULE_IDS,
                activation_scope="template_catalog",
            )
            for template in templates
        ]

    def apply_template(
        self,
        template_id: str,
        subject: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Instantiate the ESPR DPP template with ``subject`` data.

        Args:
            template_id: Must be ``"espr_dpp_v1"``.
            subject: Dict containing at minimum ``product_id`` and optional
                DPP fields (``dpp_id``, ``carrier_type``, ``registry_ref``,
                ``backup_location_uri``, ``uses_open_standard``).
            activation_scope: Tenant or scope identifier for provenance stamping.

        Returns:
            AAS Submodel dict (Release 25-01).

        Raises:
            ValueError: If ``template_id`` is not recognised.
        """
        if template_id != "espr_dpp_v1":
            raise ValueError(
                f"Unknown ESPR DPP template: {template_id!r}. "
                "Available templates: ['espr_dpp_v1']"
            )
        product_id = subject.get("product_id", "")
        submodel = build_espr_dpp_submodel(product_id=str(product_id), dpp_data=subject)
        return attach_module_provenance(
            submodel,
            module_file=__file__,
            rule_ids=_TEMPLATE_RULE_IDS,
            activation_scope=activation_scope,
        )


# ---------------------------------------------------------------------------
# Providers registry
# ---------------------------------------------------------------------------

PROVIDERS: dict[PackCapability, Any] = {
    PackCapability.REQUIREMENT_PROVIDER: EsprRequirementProvider(),
    PackCapability.EVIDENCE_AUGMENTER: EsprEvidenceAugmenter(),
    PackCapability.TWIN_TEMPLATE: EsprAasTwinTemplateProvider(),
}

__all__ = [
    "MANIFEST",
    "PROVIDERS",
    "EsprRequirementProvider",
    "EsprEvidenceAugmenter",
    "EsprAasTwinTemplateProvider",
]
