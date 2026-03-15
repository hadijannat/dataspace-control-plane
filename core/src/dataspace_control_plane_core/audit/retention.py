"""Retention rules for audit evidence."""
from __future__ import annotations

from dataclasses import dataclass

from dataspace_control_plane_core.canonical_models.enums import RetentionClass


@dataclass(frozen=True)
class RetentionPolicy:
    retention_class: RetentionClass
    purge_after_days: int | None = None
    legal_hold_required: bool = False
