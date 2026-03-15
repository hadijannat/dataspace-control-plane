"""
tests/integration/packs/activation/test_pack_activation.py
Integration tests for pack activation and capability registry.

Tests:
  1. Catena-X pack profile is not None
  2. Battery passport pack profile is not None
  3. All packs have unique pack_ids
  4. Pack registry module is importable

Requires: pack_profiles fixtures. Marker: integration
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def _get_pack_id(profile) -> str:
    """Extract pack_id from either a dict or an object."""
    if isinstance(profile, dict):
        return profile.get("pack_id", "unknown")
    return getattr(profile, "pack_id", str(type(profile).__name__))


# ---------------------------------------------------------------------------
# Test 1: Catena-X pack profile is not None
# ---------------------------------------------------------------------------


def test_catenax_pack_profile_valid(catenax_pack_profile) -> None:
    """Catena-X pack profile fixture must yield a non-None value."""
    assert catenax_pack_profile is not None, (
        "catenax_pack_profile fixture returned None — pack activation failed"
    )
    pack_id = _get_pack_id(catenax_pack_profile)
    assert pack_id, f"catenax pack profile has empty or missing pack_id: {catenax_pack_profile}"


# ---------------------------------------------------------------------------
# Test 2: Battery passport pack profile is not None
# ---------------------------------------------------------------------------


def test_battery_passport_pack_profile_valid(battery_passport_pack_profile) -> None:
    """Battery passport pack profile fixture must yield a non-None value."""
    assert battery_passport_pack_profile is not None, (
        "battery_passport_pack_profile fixture returned None"
    )
    pack_id = _get_pack_id(battery_passport_pack_profile)
    assert pack_id, f"battery_passport pack has empty pack_id: {battery_passport_pack_profile}"


# ---------------------------------------------------------------------------
# Test 3: All packs have unique pack_ids
# ---------------------------------------------------------------------------


def test_all_packs_have_unique_ids(all_pack_profiles) -> None:
    """Every registered pack profile must have a globally unique pack_id."""
    pack_ids = list(all_pack_profiles.keys())
    assert len(pack_ids) == len(set(pack_ids)), (
        f"Duplicate pack_ids detected: {[pid for pid in pack_ids if pack_ids.count(pid) > 1]}"
    )
    for pack_id in pack_ids:
        assert pack_id and pack_id != "unknown", (
            f"Pack has missing or 'unknown' pack_id in all_pack_profiles"
        )


# ---------------------------------------------------------------------------
# Test 4: Pack registry importable
# ---------------------------------------------------------------------------


def test_pack_registry_importable() -> None:
    """
    The packs registry module must be importable and expose a registry or loader.

    If packs are not yet scaffolded, this test skips gracefully.
    """
    try:
        import dataspace_control_plane_packs.registry as registry_module  # type: ignore
    except ImportError:
        pytest.skip("dataspace_control_plane_packs.registry not yet scaffolded")

    # The registry must expose some registry/loader attribute
    registry_attrs = ["registry", "loader", "REGISTRY", "get_registry", "load"]
    has_registry = any(hasattr(registry_module, attr) for attr in registry_attrs)
    assert has_registry, (
        f"packs.registry module has no registry/loader attribute. "
        f"Expected one of: {registry_attrs}. Found: {dir(registry_module)}"
    )
