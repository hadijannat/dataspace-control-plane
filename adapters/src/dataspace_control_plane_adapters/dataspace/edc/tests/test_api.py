from __future__ import annotations

import pytest

from dataspace_control_plane_adapters._shared.health import HealthStatus
from dataspace_control_plane_adapters.dataspace.edc import api as edc_api
from dataspace_control_plane_adapters.dataspace.edc.health import EdcHealthProbe
from dataspace_control_plane_adapters.dataspace.edc.mappers import (
    map_catalog_to_offer_snapshots,
    map_negotiation_state,
)
from dataspace_control_plane_adapters.dataspace.edc.raw_models import (
    EdcCatalogRaw,
    EdcDatasetRaw,
    EdcContractOfferRaw,
    EdcNegotiationRaw,
)


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


# ---------------------------------------------------------------------------
# map_negotiation_state — EDC state string → internal label
# ---------------------------------------------------------------------------

def _negotiation(state: str) -> EdcNegotiationRaw:
    return EdcNegotiationRaw.model_validate({
        "@id": "neg-1",
        "@type": "edc:ContractNegotiation",
        "edc:state": state,
    })


def test_map_negotiation_state_maps_pending_states() -> None:
    for state in ("INITIAL", "REQUESTING", "OFFERED", "ACCEPTING", "ACCEPTED"):
        assert map_negotiation_state(_negotiation(state)) == "pending"


def test_map_negotiation_state_maps_agreed_states() -> None:
    assert map_negotiation_state(_negotiation("AGREED")) == "agreed"
    assert map_negotiation_state(_negotiation("VERIFYING")) == "agreed"


def test_map_negotiation_state_maps_finalized_and_terminated() -> None:
    assert map_negotiation_state(_negotiation("FINALIZED")) == "finalized"
    assert map_negotiation_state(_negotiation("TERMINATED")) == "terminated"


def test_map_negotiation_state_returns_unknown_for_unrecognized_state() -> None:
    assert map_negotiation_state(_negotiation("BRAND_NEW_STATE")) == "unknown"


# ---------------------------------------------------------------------------
# map_catalog_to_offer_snapshots — multi-dataset and empty catalog
# ---------------------------------------------------------------------------

def _catalog(datasets: list[dict]) -> EdcCatalogRaw:
    return EdcCatalogRaw.model_validate({
        "@id": "catalog-1",
        "@type": "dcat:Catalog",
        "dcat:dataset": datasets,
    })


def test_map_catalog_returns_empty_list_for_empty_catalog() -> None:
    result = map_catalog_to_offer_snapshots(_catalog([]))
    assert result == []


def test_map_catalog_extracts_offer_snapshots_from_multiple_datasets() -> None:
    catalog = _catalog([
        {
            "@id": "asset-1",
            "odrl:hasPolicy": [
                {"@id": "offer-1", "@type": "odrl:Offer", "edc:assetId": "asset-1"},
            ],
        },
        {
            "@id": "asset-2",
            "odrl:hasPolicy": [
                {"@id": "offer-2", "@type": "odrl:Offer", "edc:assetId": "asset-2"},
                {"@id": "offer-3", "@type": "odrl:Offer", "edc:assetId": "asset-2"},
            ],
        },
    ])
    result = map_catalog_to_offer_snapshots(catalog)
    assert len(result) == 3
    assert [r["offer_id"] for r in result] == ["offer-1", "offer-2", "offer-3"]


def test_map_catalog_dataset_with_no_policy_produces_no_offers() -> None:
    catalog = _catalog([{"@id": "asset-no-policy"}])
    result = map_catalog_to_offer_snapshots(catalog)
    assert result == []
