"""
Pack activation fixtures for integration and unit tests.
Provides pre-resolved pack profiles without requiring live services.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Catena-X pack profile
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def catenax_pack_profile():
    """
    Session-scoped Catena-X pack profile.

    Tries to import and instantiate CatenaxPack from packs. Falls back to a
    static dict describing the pack capabilities if packs are not yet scaffolded.
    """
    try:
        from dataspace_control_plane_packs.catenax.api import CatenaxPack

        pack = CatenaxPack()
        yield pack
        return
    except ImportError:
        pass

    yield {
        "pack_id": "catenax",
        "version": "4.x",
        "capabilities": ["ODRL", "VCs"],
    }


# ---------------------------------------------------------------------------
# Battery passport pack profile
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def battery_passport_pack_profile():
    """
    Session-scoped battery passport pack profile.

    Tries to import BatteryPassportPack; falls back to a static dict.
    """
    try:
        from dataspace_control_plane_packs.battery_passport.api import BatteryPassportPack

        pack = BatteryPassportPack()
        yield pack
        return
    except ImportError:
        pass

    yield {
        "pack_id": "battery_passport",
        "version": "3.x",
        "capabilities": ["DPP", "Battery-Registry"],
    }


# ---------------------------------------------------------------------------
# All pack profiles
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def all_pack_profiles(catenax_pack_profile, battery_passport_pack_profile) -> dict:
    """
    Session-scoped dict mapping pack_id → profile for all known packs.
    """

    def _get_id(profile):
        if isinstance(profile, dict):
            return profile.get("pack_id", "unknown")
        return getattr(profile, "pack_id", str(type(profile).__name__))

    return {
        _get_id(catenax_pack_profile): catenax_pack_profile,
        _get_id(battery_passport_pack_profile): battery_passport_pack_profile,
    }
