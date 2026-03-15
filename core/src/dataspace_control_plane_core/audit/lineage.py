"""Lineage relationships between audit records, exports, and evidence bundles."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineageLink:
    source_id: str
    target_id: str
    relation: str
