from __future__ import annotations
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from .enums import MetricKind, TraceStatus, LogLevel


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    kind: MetricKind
    unit: str
    description: str
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    status: TraceStatus
    service_name: str

    @classmethod
    def new(cls, service_name: str) -> "TraceContext":
        """Generate a new root TraceContext with random trace/span IDs."""
        trace_id = secrets.token_hex(16)   # 128-bit trace ID as 32-char hex
        span_id = secrets.token_hex(8)     # 64-bit span ID as 16-char hex
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
    fields: dict[str, str] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
