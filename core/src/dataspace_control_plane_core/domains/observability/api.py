"""Public API surface for observability domain. Only import from here."""
from .model.enums import MetricKind, TraceStatus, LogLevel
from .model.aggregates import ObservabilityCatalog
from .model.value_objects import (
    AlertHint,
    DomainMetricDefinition,
    HealthIndicator,
    MetricDefinition,
    OperationalStatus,
    ProcedureVisibilitySnapshot,
    StructuredLogEntry,
    TelemetryAttributeSet,
    TraceContext,
)
from .metrics import (
    PROCEDURE_STARTED,
    PROCEDURE_DURATION,
    CONTRACT_NEGOTIATIONS,
    ACTIVE_ENTITLEMENTS,
    COMPLIANCE_GAPS,
    DATA_EXCHANGE_BYTES,
    ALL_METRICS,
)
from .ports import MetricEmitterPort, LogEmitterPort, TracingPort
from .commands import RecordOperationalStatusCommand
from .events import OperationalStatusRecorded
from .errors import MetricEmitterUnavailableError, TracingUnavailableError
from .services import ObservabilityService
from .model.invariants import require_non_empty_attributes

__all__ = [
    "MetricKind",
    "TraceStatus",
    "LogLevel",
    "MetricDefinition",
    "DomainMetricDefinition",
    "TraceContext",
    "StructuredLogEntry",
    "TelemetryAttributeSet",
    "ProcedureVisibilitySnapshot",
    "OperationalStatus",
    "HealthIndicator",
    "AlertHint",
    "ObservabilityCatalog",
    "RecordOperationalStatusCommand",
    "OperationalStatusRecorded",
    "ObservabilityService",
    "require_non_empty_attributes",
    "PROCEDURE_STARTED",
    "PROCEDURE_DURATION",
    "CONTRACT_NEGOTIATIONS",
    "ACTIVE_ENTITLEMENTS",
    "COMPLIANCE_GAPS",
    "DATA_EXCHANGE_BYTES",
    "ALL_METRICS",
    "MetricEmitterPort",
    "LogEmitterPort",
    "TracingPort",
    "MetricEmitterUnavailableError",
    "TracingUnavailableError",
]
