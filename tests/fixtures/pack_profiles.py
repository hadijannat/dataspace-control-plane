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
    Session-scoped Catena-X pack manifest + providers.

    Returns the real PackManifest from the catenax pack if installed,
    otherwise falls back to a static stub dict.
    """
    try:
        from dataspace_control_plane_packs.catenax.api import MANIFEST

        yield MANIFEST
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
    Session-scoped battery-passport pack manifest + providers.

    Returns the real PackManifest from the battery_passport pack if installed,
    otherwise falls back to a static stub dict.
    """
    try:
        from dataspace_control_plane_packs.battery_passport.api import MANIFEST

        yield MANIFEST
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
