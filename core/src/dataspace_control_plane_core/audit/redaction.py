"""Redaction decisions for exported or operator-visible audit data."""
from __future__ import annotations

from dataclasses import dataclass

from dataspace_control_plane_core.canonical_models.enums import RedactionClass


@dataclass(frozen=True)
class RedactionDecision:
    redaction_class: RedactionClass
    rationale: str = ""
