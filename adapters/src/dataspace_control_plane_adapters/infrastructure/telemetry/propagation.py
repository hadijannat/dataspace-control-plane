"""W3C TraceContext and B3 propagation helpers.

Provides utilities for extracting and injecting trace context from/into
HTTP headers following the W3C TraceContext and B3 propagation standards.

These helpers are used by HTTP adapters and app entry points to maintain
distributed trace correlation across service boundaries.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def extract_trace_context(headers: dict[str, str]) -> dict[str, str]:
    """Extract OTel trace context from HTTP headers.

    Looks for W3C ``traceparent``/``tracestate`` and B3 multi-format headers.
    Returns a dict of the recognised context keys for downstream use.

    Args:
        headers: HTTP header dict from an incoming request.

    Returns:
        Dict containing any extracted trace context values.
        Empty dict if no recognised trace headers are present.

    Note:
        This function does not modify the global OTel context. Use the returned
        dict to construct a canonical TraceContext for workflow correlation.
    """
    # Heavy SDK import deferred to avoid mandatory dependency at module load time.
    from opentelemetry import context as otel_context  # type: ignore[import]
    from opentelemetry.propagate import extract  # type: ignore[import]
    from opentelemetry.trace import get_current_span  # type: ignore[import]

    ctx = extract(headers)
    span = get_current_span(ctx)
    span_ctx = span.get_span_context()

    result: dict[str, str] = {}
    if span_ctx.is_valid:
        result["trace_id"] = format(span_ctx.trace_id, "032x")
        result["span_id"] = format(span_ctx.span_id, "016x")
        result["trace_flags"] = format(int(span_ctx.trace_flags), "02x")

    # Pass through W3C tracestate as-is
    if "tracestate" in headers:
        result["tracestate"] = headers["tracestate"]

    return result


def inject_trace_context(headers: dict[str, str]) -> dict[str, str]:
    """Inject W3C ``traceparent`` (and optionally ``tracestate``) into *headers*.

    Modifies the dict in-place and also returns it for chaining.
    Uses the active OTel propagator (W3C TraceContext by default).

    Args:
        headers: Mutable HTTP header dict to inject into. Modified in-place.

    Returns:
        The same *headers* dict with trace context headers added.

    Usage:
        outbound_headers = inject_trace_context({"Content-Type": "application/json"})
        await http_client.post(url, headers=outbound_headers, ...)
    """
    from opentelemetry.propagate import inject  # type: ignore[import]

    inject(headers)
    return headers


def configure_propagators() -> None:
    """Configure OTel to use W3C TraceContext and B3 multi-format propagators.

    Call this once at application startup, after the TracerProvider is set up.
    Without this call, only the default W3C TraceContext propagator is active.

    TODO: production impl — expose propagator selection via TelemetrySettings
    so operators can choose B3-only, W3C-only, or composite propagation.
    """
    from opentelemetry.propagate import set_global_textmap  # type: ignore[import]
    from opentelemetry.propagators.composite import CompositePropagator  # type: ignore[import]

    try:
        from opentelemetry.propagators.b3 import B3MultiFormat  # type: ignore[import]
        from opentelemetry.trace.propagation.tracecontext import (  # type: ignore[import]
            TraceContextTextMapPropagator,
        )
        set_global_textmap(
            CompositePropagator([TraceContextTextMapPropagator(), B3MultiFormat()])
        )
        logger.info("Configured OTel propagators: W3C TraceContext + B3MultiFormat")
    except ImportError:
        logger.warning(
            "opentelemetry-propagator-b3 not installed; falling back to W3C TraceContext only."
        )
