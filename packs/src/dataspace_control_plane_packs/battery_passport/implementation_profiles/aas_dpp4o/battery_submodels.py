"""AAS submodel templates for the EU Battery Regulation passport.

Maps battery passport obligations to AAS submodel structures following
AAS Release 25-01 and the IDTA battery passport submodel specification.

Semantic IDs are placeholders — update from the IDTA submodel catalog.
"""
from __future__ import annotations

from typing import Any

from ...._shared.implementation_profiles.aas_dpp4o.aas_release_25_01 import (
    VT_STRING, VT_BOOLEAN, VT_FLOAT, VT_DATETIME,
    minimal_submodel, property_element, submodel_element_collection,
    KIND_INSTANCE,
)

BATTERY_PASSPORT_SUBMODEL_SEMID = "https://admin-shell.io/idta/battery-passport/1/0"
BATTERY_ID_SEMID = "https://admin-shell.io/idta/battery-passport/1/0/BatteryId"


def build_battery_passport_submodel(battery_id: str, battery_data: dict[str, Any]) -> dict[str, Any]:
    """Build a battery passport AAS submodel from battery data.

    Args:
        battery_id: The unique battery identifier.
        battery_data: Dict containing battery passport fields.

    Returns:
        AAS Submodel dict in AAS Release 25-01 format.
    """
    public_elements = submodel_element_collection(
        "PublicData",
        elements=[
            property_element("BatteryId", VT_STRING,
                value=battery_id,
                semantic_id=BATTERY_ID_SEMID,
                description="Unique battery identifier"),
            property_element("ManufacturerName", VT_STRING,
                value=battery_data.get("manufacturer_name"),
                description="Battery manufacturer legal name"),
            property_element("ManufacturingDate", VT_DATETIME,
                value=battery_data.get("manufacturing_date"),
                description="Date of manufacture"),
            property_element("BatteryModel", VT_STRING,
                value=battery_data.get("battery_model"),
                description="Battery model designation"),
            property_element("CarbonFootprintKgCO2eq", VT_FLOAT,
                value=str(battery_data.get("carbon_footprint_kg_co2eq", "")),
                description="Battery carbon footprint in kg CO2 equivalent"),
        ],
        semantic_id=BATTERY_PASSPORT_SUBMODEL_SEMID,
        description="Public access fields per Annex XIII",
    )

    chemistry_elements = submodel_element_collection(
        "ChemistryInfo",
        elements=[
            property_element("BatteryChemistry", VT_STRING,
                value=battery_data.get("battery_chemistry"),
                description="Battery chemistry (e.g. NMC, LFP, solid-state)"),
            property_element("CapacityRatedKwh", VT_FLOAT,
                value=str(battery_data.get("capacity_rated_kwh", "")),
                description="Rated energy capacity in kWh"),
        ],
        description="Battery chemistry and capacity information",
    )

    lifecycle_elements = property_element(
        "LifecycleState",
        VT_STRING,
        value=battery_data.get("lifecycle_state", "active"),
        description="Current lifecycle state of the battery",
    )

    return minimal_submodel(
        submodel_id=f"urn:battery-passport:{battery_id}",
        id_short="BatteryPassport",
        kind=KIND_INSTANCE,
        semantic_id=BATTERY_PASSPORT_SUBMODEL_SEMID,
        elements=[public_elements, chemistry_elements, lifecycle_elements],
    )
