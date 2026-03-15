"""Annex XIII authority access fields (national market surveillance, customs, etc.).

These fields are available to national market surveillance authorities and customs
in addition to the public fields. Extended supply-chain, conformity, and
material-sourcing detail is included.

Reference: Regulation (EU) 2023/1542, Annex XIII
"""
from __future__ import annotations

from .public_fields import PUBLIC_FIELDS

AUTHORITY_FIELDS: list[str] = [
    *PUBLIC_FIELDS,
    "supply_chain_due_diligence_report_uri",
    "conformity_declaration_uri",
    "test_reports_uri",
    "internal_cell_chemistry_detail",
    "raw_material_sourcing_detail",
    "recycler_id",
    "waste_prevention_measures",
]
