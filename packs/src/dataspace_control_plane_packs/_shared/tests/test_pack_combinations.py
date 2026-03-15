from __future__ import annotations

from dataspace_control_plane_packs._shared.capabilities import PackCapability
from dataspace_control_plane_packs.loader import load_all_builtin_packs
from dataspace_control_plane_packs.registry import PackRegistry
from dataspace_control_plane_packs.resolver import PackResolver


def _resolve(requested_packs: list[str]):
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    return PackResolver(registry).resolve(
        activation_id="tenant:test",
        requested_packs=requested_packs,
        metadata={"core_version": "0.1.0"},
    )


def test_catenax_plus_battery_passport_matrix() -> None:
    profile = _resolve(["catenax", "battery_passport"])
    assert profile.pack_ids() == ["battery_passport", "catenax"]
    assert len(profile.providers_for(PackCapability.EVIDENCE_AUGMENTER)) == 2
    assert len(profile.providers_for(PackCapability.IDENTIFIER_SCHEME)) == 3


def test_catenax_plus_espr_dpp_matrix() -> None:
    profile = _resolve(["catenax", "espr_dpp"])
    assert profile.pack_ids() == ["espr_dpp", "catenax"]
    assert len(profile.providers_for(PackCapability.REQUIREMENT_PROVIDER)) == 2
    assert len(profile.providers_for(PackCapability.TWIN_TEMPLATE)) == 1


def test_manufacturing_x_plus_espr_dpp_matrix() -> None:
    profile = _resolve(["manufacturing_x", "espr_dpp"])
    assert profile.pack_ids() == ["espr_dpp", "manufacturing_x"]
    assert len(profile.providers_for(PackCapability.TWIN_TEMPLATE)) == 2
    assert len(profile.providers_for(PackCapability.DATA_EXCHANGE_PROFILE)) == 1


def test_gaia_x_plus_custom_federation_overlay_matrix() -> None:
    profile = _resolve(["gaia_x", "example_eu_cloud_federation"])
    assert profile.pack_ids() == ["gaia_x", "example_eu_cloud_federation"]
    provider_names = [
        type(provider).__name__
        for provider in profile.providers_for(PackCapability.TRUST_ANCHOR_OVERLAY)
    ]
    assert provider_names == [
        "GaiaXBaselineTrustAnchorOverlay",
        "ExampleFederationTrustAnchorOverlay",
    ]
