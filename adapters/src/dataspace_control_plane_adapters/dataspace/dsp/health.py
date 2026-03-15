"""Health probe for the DSP adapter family."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import DspSettings


class DspHealthProbe:
    """Configuration-backed readiness probe for the DSP protocol adapter."""

    def __init__(self, settings: DspSettings, adapter_name: str = "dsp") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="DSP callback surface configured",
            details={"callback_base_url": str(self._settings.callback_base_url)},
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "dsp",
            "capabilities": [
                "catalog_messages",
                "agreement_messages",
                "transfer_messages",
                "validators",
                "canonical_mapping",
            ],
            "spec_version": "2025-1",
            "version": "2025-1",
        }


_: HealthProbe = DspHealthProbe.__new__(DspHealthProbe)  # type: ignore[type-abstract]
