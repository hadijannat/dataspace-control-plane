"""Annex XIII legitimate-interest fields (implementing act expected by 2026-08-18).

These fields are available to economic operators and third parties with
a declared legitimate interest. The full scope of legitimate-interest access
is subject to an implementing act under Article 74 §2, expected by 2026-08-18.

Reference: Regulation (EU) 2023/1542, Annex XIII, Article 74 §2
"""
from __future__ import annotations

from .public_fields import PUBLIC_FIELDS

LEGITIMATE_INTEREST_FIELDS: list[str] = [
    *PUBLIC_FIELDS,
    "detailed_soh_history",
    "cycle_count_history",
    "detailed_cell_chemistry",
    "supply_chain_actors",
    # Note: full list subject to implementing act (Article 74 §2)
]
