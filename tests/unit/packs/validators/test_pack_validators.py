"""
tests/unit/packs/validators/test_pack_validators.py
Unit tests for pack manifest and capability validators in _shared.interfaces or _shared.manifest.

Tests: pack_id required, version required, minimal valid manifest, capability name required.
Imports packs._shared — skipped if not installed.
Marker: unit
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

# Try to import validator from known candidate modules
_validate_fn = None
_ValidationError = None
_VALIDATORS_AVAILABLE = False

for _module_path in [
    "dataspace_control_plane_packs._shared.interfaces",
    "dataspace_control_plane_packs._shared.manifest",
    "dataspace_control_plane_packs._shared.validators",
]:
    try:
        import importlib

        _mod = importlib.import_module(_module_path)
        _VALIDATORS_AVAILABLE = True
        for _fn_name in ("validate_manifest", "validate", "check_manifest"):
            if hasattr(_mod, _fn_name):
                _validate_fn = getattr(_mod, _fn_name)
                break
        for _exc_name in ("ValidationError", "ManifestError", "PackValidationError", "ValueError"):
            if hasattr(_mod, _exc_name):
                _ValidationError = getattr(_mod, _exc_name)
                break
        if _validate_fn:
            break
    except ImportError:
        continue

# Fall back to ValueError if no domain-specific error found
if _ValidationError is None:
    _ValidationError = (ValueError, TypeError, KeyError)


def _require_validators():
    if not _VALIDATORS_AVAILABLE or _validate_fn is None:
        pytest.skip("packs._shared validators not available")


def _minimal_manifest(**overrides) -> dict:
    base = {
        "pack_id": "test-pack",
        "version": "1.0.0",
        "capabilities": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Test 1: pack_id required
# ---------------------------------------------------------------------------


def test_pack_manifest_requires_pack_id() -> None:
    """Creating a manifest dict without pack_id must raise a validation error."""
    _require_validators()
    manifest = _minimal_manifest()
    del manifest["pack_id"]
    with pytest.raises(_ValidationError):
        _validate_fn(manifest)


# ---------------------------------------------------------------------------
# Test 2: version required
# ---------------------------------------------------------------------------


def test_pack_manifest_requires_version() -> None:
    """Creating a manifest dict without version must raise a validation error."""
    _require_validators()
    manifest = _minimal_manifest()
    del manifest["version"]
    with pytest.raises(_ValidationError):
        _validate_fn(manifest)


# ---------------------------------------------------------------------------
# Test 3: minimal valid manifest passes
# ---------------------------------------------------------------------------


def test_pack_manifest_valid_minimal() -> None:
    """A minimal valid manifest with pack_id, version, capabilities must pass without raising."""
    _require_validators()
    manifest = _minimal_manifest()
    # Must not raise
    result = _validate_fn(manifest)
    # Result is either True, None, or a validated object — any of these is acceptable
    assert result is not False, f"Validator returned False for a valid manifest: {manifest}"


# ---------------------------------------------------------------------------
# Test 4: capability requires name
# ---------------------------------------------------------------------------


def test_capability_requires_name() -> None:
    """A capability entry without a name field must fail validation."""
    _require_validators()
    manifest = _minimal_manifest(capabilities=[{"version": "1.0"}])  # Missing name
    with pytest.raises(_ValidationError):
        _validate_fn(manifest)
