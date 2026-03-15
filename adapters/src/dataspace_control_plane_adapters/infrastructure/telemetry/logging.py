"""OpenTelemetry log bridge adapter.

Implements core/domains/observability/ports.py LogEmitterPort using the OTel
SDK log bridge API. Emits structured log records to the configured OTLP/gRPC
collector endpoint.

Security invariant:
- Never emit raw secrets, bearer tokens, credentials, or full payload bodies.
- The StructuredLogEntry.fields dict is the only structured payload emitted;
  callers are responsible for sanitising it before constructing the entry.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import TelemetrySettings

if TYPE_CHECKING:
    from dataspace_control_plane_core.domains.observability.model.value_objects import StructuredLogEntry

logger = logging.getLogger(__name__)


class OtelLogAdapter:
    """Implements LogEmitterPort using the OpenTelemetry SDK log bridge.

    # implements core/domains/observability/ports.py LogEmitterPort

    Sets up a LoggerProvider with OTLP/gRPC log export on construction.
    The provider is registered globally via set_logger_provider().
    """

    def __init__(self, cfg: TelemetrySettings) -> None:
        self._cfg = cfg
        self._otel_logger = self._setup_logging(cfg)

    def _setup_logging(self, cfg: TelemetrySettings) -> "opentelemetry._logs.Logger":
        """Configure LoggerProvider and OTLP exporter."""
        from opentelemetry._logs import set_logger_provider, get_logger_provider  # type: ignore[import]
        from opentelemetry.sdk._logs import LoggerProvider  # type: ignore[import]
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor  # type: ignore[import]
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (  # type: ignore[import]
            OTLPLogExporter,
        )
        from .resource import build_resource

        resource = build_resource(cfg)
        exporter = OTLPLogExporter(
            endpoint=cfg.otlp_endpoint,
            insecure=cfg.insecure,
        )
        provider = LoggerProvider(resource=resource)
        provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        set_logger_provider(provider)
        return provider.get_logger(cfg.service_name, cfg.service_version)

    async def emit(self, entry: "StructuredLogEntry") -> None:
        """Emit a structured log record to the OTel log bridge.

        # implements LogEmitterPort.emit

        Translates the canonical StructuredLogEntry into an OTel LogRecord.
        The following fields are mapped:
        - entry.level       -> OTel SeverityNumber
        - entry.message     -> log body
        - entry.trace_id    -> OTel trace_id
        - entry.span_id     -> OTel span_id
        - entry.service     -> resource attribute (set at provider level)
        - entry.tenant_id   -> log attribute (safe metadata only)
        - entry.fields      -> additional log attributes (caller-sanitised)

        Security: entry.fields must not contain secrets. The caller is
        responsible for sanitisation before constructing the StructuredLogEntry.

        Args:
            entry: Canonical structured log entry from core/observability.
        """
        from opentelemetry.sdk._logs import LogRecord  # type: ignore[import]
        from opentelemetry.sdk._logs.export import LogExportResult  # type: ignore[import]
        from opentelemetry._logs import SeverityNumber  # type: ignore[import]
        from opentelemetry.trace import TraceFlags  # type: ignore[import]
        from dataspace_control_plane_core.domains.observability.model.enums import LogLevel

        severity_map: dict[LogLevel, SeverityNumber] = {
            LogLevel.DEBUG: SeverityNumber.DEBUG,
            LogLevel.INFO: SeverityNumber.INFO,
            LogLevel.WARN: SeverityNumber.WARN,
            LogLevel.ERROR: SeverityNumber.ERROR,
            LogLevel.CRITICAL: SeverityNumber.FATAL,
        }
        severity = severity_map.get(entry.level, SeverityNumber.INFO)

        attributes: dict[str, str] = {
            "tenant_id": entry.tenant_id,
            **entry.fields,  # caller-sanitised; must not contain secrets
        }

        # Reconstruct trace context integers if IDs are present
        trace_id_int = 0
        span_id_int = 0
        try:
            if entry.trace_id:
                trace_id_int = int(entry.trace_id, 16)
            if entry.span_id:
                span_id_int = int(entry.span_id, 16)
        except ValueError:
            pass  # Non-hex IDs are silently ignored

        record = LogRecord(
            timestamp=int(entry.occurred_at.timestamp() * 1e9),  # nanoseconds
            trace_id=trace_id_int,
            span_id=span_id_int,
            trace_flags=TraceFlags(TraceFlags.SAMPLED),
            severity_number=severity,
            severity_text=entry.level.value.upper(),
            body=entry.message,
            attributes=attributes,
        )

        try:
            self._otel_logger.emit(record)
        except Exception as exc:
            # Log bridge errors are non-fatal; fall back to stdlib logging.
            logger.warning("OTel log emit failed: %s", exc)
