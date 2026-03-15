"""Health probe for the Gaia-X adapter family."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import GaiaXSettings


class GaiaXHealthProbe:
    """Configuration-backed readiness probe for Gaia-X trust services."""

    def __init__(self, settings: GaiaXSettings, adapter_name: str = "gaiax") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="Gaia-X trust and compliance surfaces configured",
            details={
                "federation_id": self._settings.federation_id,
                "compliance_service_url": str(self._settings.compliance_service_url),
                "trust_anchor_registry_url": str(self._settings.trust_anchor_registry_url),
            },
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "gaia-x",
            "capabilities": [
                "self_description_client",
                "compliance_client",
                "trust_anchor_client",
                "trust_anchor_resolution",
                "credential_translation",
            ],
            "federation_id": self._settings.federation_id,
            "version": "22.10+",
        }


_: HealthProbe = GaiaXHealthProbe.__new__(GaiaXHealthProbe)  # type: ignore[type-abstract]
