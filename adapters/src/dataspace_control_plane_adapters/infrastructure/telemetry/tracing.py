"""OpenTelemetry tracing adapter.

Implements core/domains/observability/ports.py TracingPort using the OTel SDK.
Exports spans to the configured OTLP/gRPC endpoint.

Security invariant: span attributes must never contain raw secrets, credentials,
bearer tokens, or full payload bodies. Only safe metadata (IDs, status codes,
procedure types) may appear as span attributes.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import TelemetrySettings

if TYPE_CHECKING:
    from dataspace_control_plane_core.domains.observability.model.value_objects import TraceContext
    from dataspace_control_plane_core.domains.observability.model.enums import TraceStatus

logger = logging.getLogger(__name__)


class OtelTracingAdapter:
    """Implements TracingPort using the OpenTelemetry SDK.

    # implements core/domains/observability/ports.py TracingPort

    Sets up a TracerProvider with OTLP/gRPC span export on construction.
    The provider is registered globally so that propagation helpers and
    auto-instrumentation libraries pick it up automatically.
    """

    def __init__(self, cfg: TelemetrySettings) -> None:
        self._cfg = cfg
        self._tracer = self._setup_tracing(cfg)

    def _setup_tracing(self, cfg: TelemetrySettings) -> "opentelemetry.trace.Tracer":
        """Configure TracerProvider, OTLP exporter, and batch span processor."""
        from opentelemetry import trace  # type: ignore[import]
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import]
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore[import]
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore[import]
            OTLPSpanExporter,
        )
        from .resource import build_resource

        resource = build_resource(cfg)
        exporter = OTLPSpanExporter(
            endpoint=cfg.otlp_endpoint,
            insecure=cfg.insecure,
        )
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        return trace.get_tracer(cfg.service_name, cfg.service_version)

    def start_span(
        self,
        name: str,
        trace_ctx: "TraceContext | None",
    ) -> "TraceContext":
        """Start a new OTel span and return a canonical TraceContext.

        # implements TracingPort.start_span

        If *trace_ctx* is provided its trace_id and span_id are used as the
        parent context. Otherwise a new root span is started.

        Args:
            name:      Human-readable operation name.
            trace_ctx: Optional parent TraceContext from an upstream call.

        Returns:
            New TraceContext describing the started span.
        """
        from opentelemetry import trace, context  # type: ignore[import]
        from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags  # type: ignore[import]
        from dataspace_control_plane_core.domains.observability.model.value_objects import TraceContext as CoreTraceContext  # noqa: E501
        from dataspace_control_plane_core.domains.observability.model.enums import TraceStatus

        otel_context = context.get_current()

        if trace_ctx is not None:
            # Reconstruct an OTel context from the canonical TraceContext
            try:
                parent_span_ctx = SpanContext(
                    trace_id=int(trace_ctx.trace_id, 16),
                    span_id=int(trace_ctx.span_id, 16),
                    is_remote=True,
                    trace_flags=TraceFlags(TraceFlags.SAMPLED),
                )
                parent_span = NonRecordingSpan(parent_span_ctx)
                otel_context = trace.set_span_in_context(parent_span)
            except (ValueError, AttributeError):
                logger.debug("Could not reconstruct OTel context from TraceContext; using current.")

        span = self._tracer.start_span(name, context=otel_context)
        span_ctx = span.get_span_context()

        # Convert OTel IDs back to hex strings for the canonical TraceContext
        new_trace_id = format(span_ctx.trace_id, "032x")
        new_span_id = format(span_ctx.span_id, "016x")

        # Store the live span in a thread/task-local registry keyed by new_span_id
        # so end_span can retrieve it. Use a simple class-level dict.
        OtelTracingAdapter._span_registry[new_span_id] = span

        return CoreTraceContext(
            trace_id=new_trace_id,
            span_id=new_span_id,
            parent_span_id=trace_ctx.span_id if trace_ctx else None,
            status=TraceStatus.UNSET,
            service_name=self._cfg.service_name,
        )

    def end_span(
        self,
        ctx: "TraceContext",
        status: "TraceStatus",
        error: Exception | None,
    ) -> None:
        """End the OTel span associated with *ctx*.

        # implements TracingPort.end_span

        Args:
            ctx:    TraceContext returned by start_span.
            status: Final span status (OK or ERROR).
            error:  Optional exception to record on the span.
        """
        from opentelemetry.trace import StatusCode  # type: ignore[import]
        from dataspace_control_plane_core.domains.observability.model.enums import TraceStatus

        span = OtelTracingAdapter._span_registry.pop(ctx.span_id, None)
        if span is None:
            logger.warning("end_span called for unknown span_id=%s; ignoring.", ctx.span_id)
            return

        if error is not None:
            span.record_exception(error)
            span.set_status(StatusCode.ERROR, str(error))
        elif status == TraceStatus.OK:
            span.set_status(StatusCode.OK)
        elif status == TraceStatus.ERROR:
            span.set_status(StatusCode.ERROR)
        # TraceStatus.UNSET maps to leaving the status unchanged.

        span.end()

    # Class-level span registry keyed by span_id hex string.
    # In production, consider using contextvars for coroutine-safe storage.
    # TODO: production impl — replace with contextvars.ContextVar per-task storage
    _span_registry: dict[str, object] = {}
