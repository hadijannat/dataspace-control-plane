"""Health probe for the DCP adapter family."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import DcpSettings


class DcpHealthProbe:
    """Configuration-backed readiness probe for DCP surfaces.

    The DCP adapter is split across multiple trust services. This probe keeps the
    readiness contract explicit even when the caller chooses to validate the
    underlying endpoints elsewhere in deployment-specific checks.
    """

    def __init__(self, settings: DcpSettings, adapter_name: str = "dcp") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        trust_anchor_count = len(self._settings.trust_anchor_urls)
        status = HealthStatus.OK if trust_anchor_count else HealthStatus.DEGRADED
        message = (
            "DCP credential, issuer, and verifier surfaces configured"
            if trust_anchor_count
            else "DCP endpoints configured but no trust anchors declared"
        )
        return HealthReport(
            adapter=self._adapter_name,
            status=status,
            message=message,
            details={
                "credential_service_url": str(self._settings.credential_service_url),
                "issuer_service_url": str(self._settings.issuer_service_url),
                "trust_anchor_count": trust_anchor_count,
            },
        )

    def capability_descriptor(self) -> dict:
        # Internal service URLs are deliberately omitted from the capability
        # descriptor — this object may be surfaced in operator-facing or
        # inter-service responses and must not leak backend topology.
        return {
            "adapter": self._adapter_name,
            "type": "dcp",
            "capabilities": [
                "credential_service_client",
                "issuer_client",
                "presentation_verifier",
                "trust_anchor_resolution",
                "si_token_builder",
            ],
            "trust_anchor_count": len(self._settings.trust_anchor_urls),
            "version": "1.0",
        }


_: HealthProbe = DcpHealthProbe.__new__(DcpHealthProbe)  # type: ignore[type-abstract]
