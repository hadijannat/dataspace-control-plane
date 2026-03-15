"""Health probe for the Tractus-X composition adapter."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import TractuXSettings


class TractuXHealthProbe:
    """Configuration-backed readiness probe for Tractus-X composition surfaces."""

    def __init__(self, settings: TractuXSettings, adapter_name: str = "tractusx") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="Tractus-X discovery and environment conventions configured",
            details={
                "environment": self._settings.environment,
                "dataspace_discovery_url": str(self._settings.dataspace_discovery_url),
            },
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "tractusx",
            "capabilities": [
                "discovery",
                "bpn_resolution",
                "service_directory",
                "environment_conventions",
            ],
            "environment": self._settings.environment,
            "version": "0.1.0",
        }


_: HealthProbe = TractuXHealthProbe.__new__(TractuXHealthProbe)  # type: ignore[type-abstract]
