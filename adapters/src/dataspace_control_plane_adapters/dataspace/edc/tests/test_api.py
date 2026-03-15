from __future__ import annotations

import pytest

from dataspace_control_plane_adapters._shared.health import HealthStatus
from dataspace_control_plane_adapters.dataspace.edc import api as edc_api
from dataspace_control_plane_adapters.dataspace.edc.health import EdcHealthProbe


class _HealthyManagementClient:
    async def get(self, _path: str) -> list[object]:
        return []


def test_public_api_hides_wire_models_and_mapper_helpers() -> None:
    leaked_symbols = {
        "EdcAssetRaw",
        "EdcCatalogRaw",
        "map_asset_to_ref",
        "map_catalog_to_offer_snapshots",
        "map_transfer_event",
        "TransferDecoration",
    }

    assert leaked_symbols.isdisjoint(edc_api.__all__)


@pytest.mark.asyncio
async def test_health_probe_exposes_capabilities_without_extra_state() -> None:
    probe = EdcHealthProbe(_HealthyManagementClient())

    report = await probe.check()
    descriptor = probe.capability_descriptor()

    assert report.status is HealthStatus.OK
    assert "catalog" in descriptor["capabilities"]
