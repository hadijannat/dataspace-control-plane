"""Public API surface for the telemetry infrastructure adapter.

Import only from this module when wiring the adapter in apps/ container code.
Internal implementation modules are considered private.

Example:
    from dataspace_control_plane_adapters.infrastructure.telemetry.api import (
        make_telemetry_ports,
        TelemetrySettings,
        OtelTracingAdapter,
        OtelMetricAdapter,
        OtelLogAdapter,
    )
    cfg = TelemetrySettings()
    ports = make_telemetry_ports(cfg)
"""
from __future__ import annotations

from .config import TelemetrySettings
from .errors import TelemetryError, TelemetryExportError, TelemetryInitError
from .health import TelemetryHealthProbe
from .logging import OtelLogAdapter
from .metrics import OtelMetricAdapter
from .ports_impl import make_telemetry_ports
from .tracing import OtelTracingAdapter

__all__ = [
    # Configuration
    "TelemetrySettings",
    # Errors
    "TelemetryError",
    "TelemetryExportError",
    "TelemetryInitError",
    "TelemetryHealthProbe",
    # Concrete adapters
    "OtelTracingAdapter",
    "OtelMetricAdapter",
    "OtelLogAdapter",
    # Factory
    "make_telemetry_ports",
]
