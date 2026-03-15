"""Invariants for observability semantic models."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.errors import ValidationError

from .value_objects import TelemetryAttributeSet


def require_non_empty_attributes(attributes: TelemetryAttributeSet) -> None:
    if not attributes.attributes:
        raise ValidationError("TelemetryAttributeSet must define at least one attribute")
