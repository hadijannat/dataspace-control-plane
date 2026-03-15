from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.domains._shared.ids import TenantId, default_id_factory
from dataspace_control_plane_core.domains._shared.time import utc_now

from .enums import MetricKind, TraceStatus, LogLevel


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    kind: MetricKind
    unit: str
    description: str
    labels: tuple[str, ...] = ()


DomainMetricDefinition = MetricDefinition


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    status: TraceStatus
    service_name: str

    @classmethod
    def new(cls, service_name: str) -> "TraceContext":
        """Compatibility helper backed by the shared ID factory."""
        trace_id = default_id_factory().new_request_id().replace("-", "")
        span_id = default_id_factory().new_request_id().replace("-", "")[:16]
        return cls(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            status=TraceStatus.UNSET,
            service_name=service_name,
        )


@dataclass(frozen=True)
class StructuredLogEntry:
    level: LogLevel
    message: str
    service: str
    trace_id: str
    span_id: str
    tenant_id: str
    fields: dict[str, str] = field(default_factory=dict, hash=False)
    occurred_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class TelemetryAttributeSet:
    attributes: dict[str, str] = field(default_factory=dict, hash=False)


@dataclass(frozen=True)
class ProcedureVisibilitySnapshot:
    workflow_id: str
    correlation: CorrelationContext
    business_status: str
    technical_status: str


@dataclass(frozen=True)
class OperationalStatus:
    code: str
    kind: str
    description: str


@dataclass(frozen=True)
class HealthIndicator:
    name: str
    healthy: bool
    detail: str = ""


@dataclass(frozen=True)
class AlertHint:
    code: str
    severity: str
    summary: str
