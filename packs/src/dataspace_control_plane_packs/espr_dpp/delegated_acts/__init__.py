"""Namespace for product-group specific delegated act rule sets.

Each product group gets its own subpackage. All delegated act packages
must be effective-dated and independently versioned.

Product-group delegated act subpackages must declare:
  - DELEGATED_ACT_ID: str
  - EFFECTIVE_FROM: str  (ISO 8601 date)
  - EFFECTIVE_TO: str | None
  - RULES: list[RuleDefinition]
"""
from __future__ import annotations
