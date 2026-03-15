"""
Template for an ESPR delegated act pack.

Copy this package, rename it to the product group identifier, and populate
the RULES list with product-group-specific RuleDefinition objects.

Required attributes:
  DELEGATED_ACT_ID: str
  EFFECTIVE_FROM: str  (ISO 8601 date)
  EFFECTIVE_TO: str | None
  RULES: list[RuleDefinition]
"""
from __future__ import annotations

DELEGATED_ACT_ID = "template"
EFFECTIVE_FROM = "2026-01-01"
EFFECTIVE_TO = None
RULES: list = []
