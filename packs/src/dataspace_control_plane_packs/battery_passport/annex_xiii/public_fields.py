"""Annex XIII public access fields (accessible to anyone with QR/identifier scan).

These fields are available to any party that scans the QR code or uses the
battery unique identifier. No authentication or declared interest required.

Reference: Regulation (EU) 2023/1542, Annex XIII
"""
from __future__ import annotations

PUBLIC_FIELDS: list[str] = [
    "battery_id",
    "manufacturer_name",
    "manufacturing_date",
    "manufacturing_place",
    "battery_model",
    "battery_chemistry",
    "capacity_rated_kwh",
    "state_of_health_pct",
    "carbon_footprint_kg_co2eq",
    "hazardous_substances_flag",
    "recycled_content_pct",
    "dpp_link",
    "qr_code_uri",
]
