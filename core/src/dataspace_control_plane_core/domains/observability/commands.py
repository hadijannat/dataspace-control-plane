"""Commands for observability semantic state."""
from __future__ import annotations

from dataclasses import dataclass

from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext

from .model.value_objects import OperationalStatus


@dataclass(frozen=True)
class RecordOperationalStatusCommand:
    status: OperationalStatus
    correlation: CorrelationContext
