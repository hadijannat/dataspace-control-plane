"""AAS/DPP4.0 bridge for Manufacturing-X twin templates.

Implements :class:`TwinTemplateProvider` using the shared AAS DPP4.0
implementation profile to generate nameplate and MX-specific submodel
templates for Manufacturing-X assets.

No HTTP, DB, or Temporal code here.
"""
from __future__ import annotations

from typing import Any

from .._shared.implementation_profiles.aas_dpp4o.api import (
    AAS_RELEASE,
    AasId,
    KIND_TEMPLATE,
    minimal_submodel,
    property_element,
)
from .._shared.implementation_profiles.aas_dpp4o.submodel_catalog import (
    SEMID_NAMEPLATE,
    nameplate_template,
)

# MX-specific semantic IDs (placeholders — update from IDTA/MX registry)
_SEMID_MX_CAPABILITY = "https://admin-shell.io/manufacturing-x/capability/1/0/Capability"
_SEMID_MX_PROFILE = "https://admin-shell.io/manufacturing-x/profile/1/0/Profile"

_MX_PACK_VERSION = "1.0.0"

# Template descriptor keys
_TMPL_NAMEPLATE = "mx:nameplate"
_TMPL_MX_CAPABILITY = "mx:capability-declaration"


class MxTwinTemplateProvider:
    """Provides AAS twin templates for Manufacturing-X assets.

    Templates are derived from the AAS DPP4.0 shared profile and augmented
    with MX-specific submodel declarations.  All templates are returned in
    AAS Part 1 JSON-compatible dict form.
    """

    # ------------------------------------------------------------------
    # TwinTemplateProvider interface
    # ------------------------------------------------------------------

    def templates(self, *, context: dict[str, Any]) -> list[dict[str, Any]]:  # noqa: ARG002
        """Return template descriptors for MX assets.

        Each descriptor has at minimum ``template_id``, ``name``, and
        ``semantic_id`` keys.
        """
        return [
            {
                "template_id": _TMPL_NAMEPLATE,
                "name": "MX Asset Nameplate",
                "semantic_id": SEMID_NAMEPLATE,
                "aas_release": AAS_RELEASE,
                "kind": KIND_TEMPLATE,
                "description": (
                    "Standard IDTA Nameplate submodel template for Manufacturing-X assets."
                ),
            },
            {
                "template_id": _TMPL_MX_CAPABILITY,
                "name": "MX Capability Declaration",
                "semantic_id": _SEMID_MX_CAPABILITY,
                "aas_release": AAS_RELEASE,
                "kind": KIND_TEMPLATE,
                "description": (
                    "Declares the MX-Port layers and protocols supported by this asset."
                ),
            },
        ]

    def apply_template(
        self,
        template_id: str,
        subject: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Instantiate a template for ``subject``.

        Supported template IDs:
          - ``mx:nameplate`` — IDTA Nameplate submodel
          - ``mx:capability-declaration`` — MX capability submodel

        Args:
            template_id:      One of the IDs returned by :meth:`templates`.
            subject:          Dict with asset fields (``id``, ``manufacturer_name``, etc.).
            activation_scope: Tenant/scope that triggered generation.

        Returns:
            AAS Part 1 Submodel dict.

        Raises:
            KeyError: If ``template_id`` is not recognized.
        """
        if template_id == _TMPL_NAMEPLATE:
            return self._apply_nameplate(subject, activation_scope)
        if template_id == _TMPL_MX_CAPABILITY:
            return self._apply_capability_declaration(subject, activation_scope)
        raise KeyError(
            f"Unknown MX twin template id: {template_id!r}. "
            f"Available: {_TMPL_NAMEPLATE!r}, {_TMPL_MX_CAPABILITY!r}"
        )

    # ------------------------------------------------------------------
    # Template builders
    # ------------------------------------------------------------------

    def _apply_nameplate(
        self,
        subject: dict[str, Any],
        activation_scope: str,
    ) -> dict[str, Any]:
        """Build a minimal IDTA Nameplate submodel for an MX asset."""
        asset_id = str(subject.get("id", f"urn:mx:asset:{activation_scope}:unknown"))
        sm = nameplate_template(asset_id)
        # Stamp MX-specific context
        sm["mx:pack_version"] = _MX_PACK_VERSION
        sm["mx:activation_scope"] = activation_scope
        # Populate known fields from subject
        for el in sm.get("submodelElements", []):
            id_short = el.get("idShort", "")
            if id_short == "ManufacturerName" and "manufacturer_name" in subject:
                el["value"] = str(subject["manufacturer_name"])
            elif id_short == "ManufacturerProductDesignation" and "product_designation" in subject:
                el["value"] = str(subject["product_designation"])
            elif id_short == "SerialNumber" and "serial_number" in subject:
                el["value"] = str(subject["serial_number"])
        return sm

    def _apply_capability_declaration(
        self,
        subject: dict[str, Any],
        activation_scope: str,
    ) -> dict[str, Any]:
        """Build an MX Capability Declaration submodel."""
        asset_id = str(subject.get("id", f"urn:mx:asset:{activation_scope}:unknown"))
        profile_name = str(subject.get("profile_name", "unknown"))
        layers = subject.get("layers", [])
        protocols = subject.get("protocols", [])

        elements = [
            property_element(
                "ProfileName",
                "xs:string",
                value=profile_name,
                semantic_id=_SEMID_MX_PROFILE,
                description="Manufacturing-X / Factory-X reference profile name.",
            ),
            property_element(
                "ActiveLayers",
                "xs:string",
                value=",".join(layers) if isinstance(layers, list) else str(layers),
                description="Comma-separated list of active MX-Port layers.",
            ),
            property_element(
                "SupportedProtocols",
                "xs:string",
                value=",".join(protocols) if isinstance(protocols, list) else str(protocols),
                description="Comma-separated list of supported MX-Port protocols.",
            ),
            property_element(
                "PackVersion",
                "xs:string",
                value=_MX_PACK_VERSION,
                description="Version of the Manufacturing-X pack that generated this declaration.",
            ),
        ]

        return minimal_submodel(
            submodel_id=f"{asset_id}/mx-capability",
            id_short="MxCapabilityDeclaration",
            elements=elements,
            semantic_id=_SEMID_MX_CAPABILITY,
            kind=KIND_TEMPLATE,
        )
