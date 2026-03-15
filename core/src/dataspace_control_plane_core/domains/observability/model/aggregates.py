"""Aggregate-like container for observability semantics."""
from __future__ import annotations

from dataclasses import dataclass, field

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot

from .value_objects import DomainMetricDefinition, OperationalStatus


@dataclass
class ObservabilityCatalog(AggregateRoot):
    statuses: list[OperationalStatus] = field(default_factory=list)
    metrics: list[DomainMetricDefinition] = field(default_factory=list)

    def register_status(self, status: OperationalStatus) -> None:
        self.statuses = [current for current in self.statuses if current.code != status.code]
        self.statuses.append(status)
