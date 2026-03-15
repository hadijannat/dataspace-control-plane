"""Catalog of standard AAS submodel templates for DPP4.0 profiles.

Submodel semantic IDs are sourced from IDTA submodel specifications.
These are placeholders with the correct shape — actual semantic IDs must
be updated from the IDTA submodel catalog once pinned.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .aas_release_25_01 import (
    KIND_TEMPLATE,
    SME_PROPERTY,
    VT_STRING,
    VT_DATETIME,
    minimal_submodel,
    property_element,
    submodel_element_collection,
)


# ---------------------------------------------------------------------------
# Canonical submodel semantic IDs (IDTA registry placeholders)
# ---------------------------------------------------------------------------

SEMID_NAMEPLATE = "https://admin-shell.io/idta/nameplate/2/0/Nameplate"
SEMID_TECHNICAL_DATA = "https://admin-shell.io/idta/technical-data/1/2/TechnicalData"
SEMID_HANDOVER_DOC = "https://admin-shell.io/idta/handover-documentation/1/1/HandoverDocumentation"
SEMID_CARBON_FOOTPRINT = "https://admin-shell.io/idta/carbon-footprint/0/9/CarbonFootprint"
SEMID_DIGITAL_NAMEPLATE = "https://admin-shell.io/zvei/nameplate/2/0/Nameplate"


@dataclass(frozen=True)
class SubmodelEntry:
    """Catalog entry for a well-known AAS submodel."""

    id_short: str
    semantic_id: str
    description: str
    optional: bool = False


STANDARD_SUBMODELS: dict[str, SubmodelEntry] = {
    "nameplate": SubmodelEntry(
        id_short="Nameplate",
        semantic_id=SEMID_NAMEPLATE,
        description="Manufacturer nameplate information",
    ),
    "technical_data": SubmodelEntry(
        id_short="TechnicalData",
        semantic_id=SEMID_TECHNICAL_DATA,
        description="Technical properties and parameters",
        optional=True,
    ),
    "handover_documentation": SubmodelEntry(
        id_short="HandoverDocumentation",
        semantic_id=SEMID_HANDOVER_DOC,
        description="Handover/installation documentation",
        optional=True,
    ),
    "carbon_footprint": SubmodelEntry(
        id_short="CarbonFootprint",
        semantic_id=SEMID_CARBON_FOOTPRINT,
        description="Product carbon footprint (PCF) data",
        optional=True,
    ),
}


def nameplate_template(asset_id: str) -> dict[str, Any]:
    """Build a nameplate submodel template for the given asset."""
    return minimal_submodel(
        submodel_id=f"{asset_id}/nameplate",
        id_short="Nameplate",
        kind=KIND_TEMPLATE,
        semantic_id=SEMID_NAMEPLATE,
        elements=[
            property_element("ManufacturerName", VT_STRING, semantic_id="0173-1#02-AAO677#002"),
            property_element("ManufacturerProductDesignation", VT_STRING, semantic_id="0173-1#02-AAW338#001"),
            property_element("SerialNumber", VT_STRING, semantic_id="0173-1#02-AAM556#002"),
            property_element("ManufacturingDate", VT_DATETIME, semantic_id="0173-1#02-AAR972#002"),
            property_element("BatchId", VT_STRING, semantic_id="0173-1#02-AAQ227#002", optional=True),
        ],
    )


def property_element(
    id_short: str,
    value_type: str,
    *,
    semantic_id: str | None = None,
    optional: bool = False,
    description: str | None = None,
) -> dict[str, Any]:
    """Wrap the base property_element with optional flag in category."""
    from .aas_release_25_01 import property_element as _pe, CATEGORY_PARAMETER, CATEGORY_VARIABLE
    cat = CATEGORY_VARIABLE if optional else CATEGORY_PARAMETER
    return _pe(id_short, value_type, semantic_id=semantic_id, description=description, category=cat)
