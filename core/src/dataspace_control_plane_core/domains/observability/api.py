"""Public API surface for observability domain. Only import from here."""
from .model.enums import MetricKind, TraceStatus, LogLevel
from .model.value_objects import MetricDefinition, TraceContext, StructuredLogEntry
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
from .errors import MetricEmitterUnavailableError, TracingUnavailableError

__all__ = [
    "MetricKind",
    "TraceStatus",
    "LogLevel",
    "MetricDefinition",
    "TraceContext",
    "StructuredLogEntry",
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
