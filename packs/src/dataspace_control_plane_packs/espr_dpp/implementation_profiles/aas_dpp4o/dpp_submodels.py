"""AAS DPP4.0 submodel templates for ESPR DPP obligations.

Maps the core ESPR DPP obligations (identifier, carrier, registry, backup,
accessibility) to AAS submodel elements using the shared AAS DPP4.0 profile.

Normative reference: IDTA AAS Specification Release 25-01
Regulation reference: Regulation (EU) 2024/1781 (ESPR)
"""
from __future__ import annotations

from typing import Any

from ...._shared.implementation_profiles.aas_dpp4o.api import (
    AAS_RELEASE,
    minimal_submodel,
    property_element,
    submodel_element_collection,
)
from ...._shared.implementation_profiles.aas_dpp4o.aas_release_25_01 import (
    VT_BOOLEAN,
    VT_STRING,
    VT_URI,
)

ESPR_DPP_SUBMODEL_ID = "https://admin-shell.io/idta/espr-dpp/1/0"
ESPR_DPP_SEMANTIC_ID = "https://admin-shell.io/idta/espr-dpp/SubmodelTemplate/1/0"


def build_espr_dpp_submodel(product_id: str, dpp_data: dict[str, Any]) -> dict[str, Any]:
    """Build an AAS Submodel envelope for ESPR DPP obligations.

    Args:
        product_id: ISO/IEC 15459-compliant product identifier. Used as
            the submodel instance identifier suffix.
        dpp_data: Dict with DPP field values. Recognised keys:
            - ``dpp_id``: str — DPP unique identifier
            - ``carrier_type``: str — physical data carrier type
            - ``registry_ref``: str — Commission registry reference URL
            - ``backup_location_uri``: str — backup storage URI
            - ``uses_open_standard``: bool — open standards compliance flag
            - ``regulation_version``: str — defaults to "2024/1781"

    Returns:
        A plain dict conforming to AAS Submodel structure (Release 25-01).
    """
    instance_id = f"{ESPR_DPP_SUBMODEL_ID}/{product_id}"

    elements = [
        property_element(
            "ProductId",
            VT_STRING,
            value=product_id,
            semantic_id="https://admin-shell.io/idta/espr-dpp/ProductId/1/0",
            description="ISO/IEC 15459-compatible unique product identifier",
        ),
        property_element(
            "DppId",
            VT_STRING,
            value=dpp_data.get("dpp_id"),
            semantic_id="https://admin-shell.io/idta/espr-dpp/DppId/1/0",
            description="Unique Digital Product Passport identifier",
        ),
        property_element(
            "CarrierType",
            VT_STRING,
            value=dpp_data.get("carrier_type"),
            semantic_id="https://admin-shell.io/idta/espr-dpp/CarrierType/1/0",
            description="Physical data carrier type (qr_code, rfid, data_matrix, nfc)",
        ),
        property_element(
            "RegistryRef",
            VT_URI,
            value=dpp_data.get("registry_ref"),
            semantic_id="https://admin-shell.io/idta/espr-dpp/RegistryRef/1/0",
            description="Reference URL to the Commission registry entry",
        ),
        property_element(
            "BackupRef",
            VT_URI,
            value=dpp_data.get("backup_location_uri"),
            semantic_id="https://admin-shell.io/idta/espr-dpp/BackupRef/1/0",
            description="URI of the DPP backup copy storage location",
        ),
        property_element(
            "OpenStandards",
            VT_BOOLEAN,
            value=str(dpp_data.get("uses_open_standard", False)).lower(),
            semantic_id="https://admin-shell.io/idta/espr-dpp/OpenStandards/1/0",
            description="Declares that the DPP uses open, interoperable standards",
        ),
        property_element(
            "RegulationVersion",
            VT_STRING,
            value=dpp_data.get("regulation_version", "2024/1781"),
            semantic_id="https://admin-shell.io/idta/espr-dpp/RegulationVersion/1/0",
            description="ESPR regulation version (EU 2024/1781)",
        ),
    ]

    return minimal_submodel(
        submodel_id=instance_id,
        id_short="EsprDpp",
        elements=elements,
        semantic_id=ESPR_DPP_SEMANTIC_ID,
    )
