"""Health probe for the Temporal client adapter."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import TemporalClientSettings


class TemporalHealthProbe:
    """Configuration-backed readiness probe for the Temporal client wrapper.

    Connectivity is already verified during ``create_temporal_client``. This
    probe keeps the adapter health surface explicit without re-opening an
    additional gRPC connection for every readiness check.
    """

    def __init__(
        self,
        settings: TemporalClientSettings,
        adapter_name: str = "temporal_client",
    ) -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="Temporal client configuration loaded",
            details={
                "host": self._settings.host,
                "port": self._settings.port,
                "namespace": self._settings.namespace,
                "default_task_queue": self._settings.default_task_queue,
            },
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "temporal",
            "capabilities": [
                "workflow_gateway",
                "signals",
                "queries",
                "updates",
                "schedules",
            ],
            "namespace": self._settings.namespace,
            "default_task_queue": self._settings.default_task_queue,
            "version": "1.7+",
        }


_: HealthProbe = TemporalHealthProbe.__new__(TemporalHealthProbe)  # type: ignore[type-abstract]
