"""Health probe for the Siemens Teamcenter adapter."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import TeamcenterSettings


class TeamcenterHealthProbe:
    """Configuration-backed readiness probe for Teamcenter exports."""

    def __init__(self, settings: TeamcenterSettings, adapter_name: str = "siemens_teamcenter") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="Teamcenter export configuration loaded",
            details={"base_url": str(self._settings.base_url)},
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "teamcenter",
            "capabilities": [
                "client",
                "bom_extract",
                "item_revision_extract",
                "document_extract",
                "checkpointing",
            ],
            "chunk_size": self._settings.chunk_size,
            "version": "0.1.0",
        }


_: HealthProbe = TeamcenterHealthProbe.__new__(TeamcenterHealthProbe)  # type: ignore[type-abstract]
