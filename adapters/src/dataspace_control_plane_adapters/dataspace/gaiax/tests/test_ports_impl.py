from __future__ import annotations

import pytest

from dataspace_control_plane_adapters._shared.health import HealthStatus
from dataspace_control_plane_adapters.dataspace.gaiax import api as gaiax_api
from dataspace_control_plane_adapters.dataspace.gaiax.health import GaiaXHealthProbe
from dataspace_control_plane_adapters.dataspace.gaiax import ports_impl as gaiax_ports
from dataspace_control_plane_adapters.dataspace.gaiax.config import GaiaXSettings
from dataspace_control_plane_core.canonical_models.identity import DidUri
from dataspace_control_plane_core.domains.machine_trust.model.value_objects import (
    TrustAnchor,
)


def _settings() -> GaiaXSettings:
    return GaiaXSettings(
        compliance_service_url="https://compliance.example.com",
        trust_anchor_registry_url="https://trust-registry.example.com",
        federation_id="gaia-x-eu",
    )


class _FakeTrustAnchorClient:
    def __init__(self, _cfg: GaiaXSettings) -> None:
        self.federations: list[str] = []

    async def list_trust_anchors(self, federation_id: str) -> list[dict[str, object]]:
        self.federations.append(federation_id)
        return [
            {"name": "AISBL", "did": "did:web:gaia-x.eu", "active": True},
            {"name": "inactive", "did": "did:web:inactive.example.com", "active": False},
            {"name": "missing-did", "active": True},
        ]


@pytest.mark.asyncio
async def test_trust_anchor_resolver_returns_core_value_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gaiax_ports, "GaiaXTrustAnchorClient", _FakeTrustAnchorClient)

    resolver = gaiax_ports.GaiaXTrustAnchorAdapterPort(_settings())
    anchors = await resolver.list_active("gaia-x")

    assert anchors == [
        TrustAnchor(
            name="AISBL",
            did=DidUri(uri="did:web:gaia-x.eu"),
            trust_scope="gaia-x",
            is_active=True,
        )
    ]


@pytest.mark.asyncio
async def test_gaiax_health_probe_exposes_federation_capability() -> None:
    probe = GaiaXHealthProbe(_settings())

    report = await probe.check()
    descriptor = probe.capability_descriptor()

    assert report.status is HealthStatus.OK
    assert descriptor["federation_id"] == "gaia-x-eu"


def test_public_api_hides_translation_helpers() -> None:
    assert {
        "translate_participant_credential",
        "translate_compliance_credential",
    }.isdisjoint(gaiax_api.__all__)
