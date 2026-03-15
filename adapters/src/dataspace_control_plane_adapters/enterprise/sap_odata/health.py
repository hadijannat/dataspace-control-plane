"""Health probe for the SAP OData adapter."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import SapOdataSettings


class SapOdataHealthProbe:
    """Configuration-backed readiness probe for SAP OData extraction."""

    def __init__(self, settings: SapOdataSettings, adapter_name: str = "sap_odata") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="SAP OData service configuration loaded",
            details={"service_url": str(self._settings.service_url)},
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "odata",
            "capabilities": [
                "metadata_client",
                "query_compilation",
                "extractor",
                "checkpointing",
            ],
            "service_url": str(self._settings.service_url),
            "version": "4.01",
        }


_: HealthProbe = SapOdataHealthProbe.__new__(SapOdataHealthProbe)  # type: ignore[type-abstract]
