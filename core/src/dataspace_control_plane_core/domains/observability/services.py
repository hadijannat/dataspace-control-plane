"""Services for observability semantic definitions."""
from __future__ import annotations

from .model.aggregates import ObservabilityCatalog
from .model.value_objects import OperationalStatus


class ObservabilityService:
    def register_status(self, catalog: ObservabilityCatalog, status: OperationalStatus) -> ObservabilityCatalog:
        catalog.register_status(status)
        return catalog
