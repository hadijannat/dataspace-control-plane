from __future__ import annotations

import pytest

from dataspace_control_plane_adapters._shared.health import HealthStatus
from dataspace_control_plane_adapters.dataspace.dsp import api as dsp_api
from dataspace_control_plane_adapters.dataspace.dsp.config import DspSettings
from dataspace_control_plane_adapters.dataspace.dsp.health import DspHealthProbe


def _settings() -> DspSettings:
    return DspSettings(callback_base_url="https://control-plane.example.com/dsp")


def test_public_api_hides_wire_messages_and_mapping_helpers() -> None:
    leaked_symbols = {
        "DspCatalogRequest",
        "DspTransferRequestMessage",
        "validate_catalog_request",
        "map_catalog_to_offers",
    }

    assert leaked_symbols.isdisjoint(dsp_api.__all__)


@pytest.mark.asyncio
async def test_health_probe_reports_protocol_capabilities() -> None:
    probe = DspHealthProbe(_settings())

    report = await probe.check()
    descriptor = probe.capability_descriptor()

    assert report.status is HealthStatus.OK
    assert descriptor["spec_version"] == "2025-1"
