"""Health probe for the telemetry adapter."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import TelemetrySettings


class TelemetryHealthProbe:
    """Configuration-backed readiness probe for OTLP emission."""

    def __init__(self, settings: TelemetrySettings, adapter_name: str = "telemetry") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="Telemetry exporter configuration loaded",
            details={"otlp_endpoint": self._settings.otlp_endpoint},
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "otel",
            "capabilities": [
                "metric_emitter",
                "log_emitter",
                "tracing",
                "propagation",
                "resource_builder",
            ],
            "service_name": self._settings.service_name,
            "otlp_endpoint": self._settings.otlp_endpoint,
            "version": self._settings.service_version,
        }


_: HealthProbe = TelemetryHealthProbe.__new__(TelemetryHealthProbe)  # type: ignore[type-abstract]
