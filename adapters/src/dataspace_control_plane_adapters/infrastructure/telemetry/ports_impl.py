"""Telemetry port implementations factory.

Constructs and returns all three core/observability port implementations
from a single TelemetrySettings instance.

Usage:
    from dataspace_control_plane_adapters.infrastructure.telemetry.ports_impl import (
        make_telemetry_ports,
    )
    cfg = TelemetrySettings()
    ports = make_telemetry_ports(cfg)
    metric_emitter = ports["metric_emitter"]
    log_emitter = ports["log_emitter"]
    tracing = ports["tracing"]
"""
from __future__ import annotations

from .config import TelemetrySettings


def make_telemetry_ports(cfg: TelemetrySettings) -> dict[str, object]:
    """Construct all telemetry port implementations from *cfg*.

    Ports returned:
        "metric_emitter" — OtelMetricAdapter (implements MetricEmitterPort)
        "log_emitter"    — OtelLogAdapter    (implements LogEmitterPort)
        "tracing"        — OtelTracingAdapter (implements TracingPort)

    All three OTel providers (TracerProvider, MeterProvider, LoggerProvider)
    are registered globally during construction so that auto-instrumentation
    libraries and propagation helpers pick them up automatically.

    Args:
        cfg: TelemetrySettings populated from environment or defaults.

    Returns:
        Dict keyed by port role name, values are the concrete adapter instances.

    Raises:
        TelemetryInitError: Any OTel SDK initialisation failure.
    """
    # Deferred imports keep heavy SDK loads out of module-level evaluation.
    from .metrics import OtelMetricAdapter
    from .logging import OtelLogAdapter
    from .tracing import OtelTracingAdapter

    return {
        "metric_emitter": OtelMetricAdapter(cfg),
        "log_emitter": OtelLogAdapter(cfg),
        "tracing": OtelTracingAdapter(cfg),
    }
