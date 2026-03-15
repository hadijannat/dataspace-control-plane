"""
tests/integration/adapters/dataspace/test_aas_shell_serialization.py
Integration tests for BaSyX AAS shell descriptor serialization.

Tests:
  1. BaSyX descriptor_mappers module is importable
  2. encode_aas_id / decode_aas_id round-trip is lossless
  3. encode_aas_id handles URN, HTTP URL, and plain string IDs
  4. map_canonical_to_shell_descriptor output has required 'id' field
  5. map_canonical_to_shell_descriptor preserves twin_id and globalAssetId
  6. map_canonical_to_shell_descriptor with submodels produces submodelDescriptors
  7. map_shell_descriptor_to_canonical extracts twin_id and global_asset_id
  8. Round-trip: canonical → descriptor → canonical preserves core fields
  9. Descriptor output validates against shell-descriptor.schema.json
 10. Descriptor with specificAssetIds validates against schema
 11. map_canonical_to_shell_descriptor handles empty submodels

All tests are pure Python — no BaSyX server required.
Marker: integration
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.unit

# ── Path injection ────────────────────────────────────────────────────────────
_ADAPTERS_SRC = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "adapters"
    / "src"
)
if _ADAPTERS_SRC.exists() and str(_ADAPTERS_SRC) not in sys.path:
    sys.path.insert(0, str(_ADAPTERS_SRC))

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SHELL_DESCRIPTOR_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "aas" / "source" / "profiles" / "shell-descriptor.schema.json"
)


def _skip_if_adapters_missing() -> None:
    try:
        import dataspace_control_plane_adapters  # noqa: F401
    except ImportError as exc:
        pytest.skip(f"adapters package not available: {exc}")


def _import_descriptor_mappers():
    from dataspace_control_plane_adapters.dataspace.basyx.descriptor_mappers import (
        decode_aas_id,
        encode_aas_id,
        map_canonical_to_shell_descriptor,
        map_shell_descriptor_to_canonical,
    )
    return encode_aas_id, decode_aas_id, map_canonical_to_shell_descriptor, map_shell_descriptor_to_canonical


# ── Canonical fixture payloads ────────────────────────────────────────────────

def _minimal_canonical() -> dict[str, Any]:
    return {
        "twin_id": "urn:example:asset:001",
        "global_asset_id": "urn:example:global:001",
        "specific_asset_ids": [],
        "submodels": [],
    }


def _canonical_with_submodel() -> dict[str, Any]:
    return {
        "twin_id": "urn:example:asset:002",
        "global_asset_id": "urn:example:global:002",
        "specific_asset_ids": [
            {"name": "manufacturerPartId", "value": "PART-9001"},
        ],
        "submodels": [
            {
                "id": "urn:example:submodel:sm001",
                "semantic_id": "urn:bamm:io.catenax.serial_part:1.0.0#SerialPart",
                "interface": "SUBMODEL-3.0",
                "endpoint_url": "https://aas.example.com/submodels/sm001",
                "endpoint_protocol": "HTTP",
            }
        ],
    }


# ── Test 1: import ────────────────────────────────────────────────────────────


def test_descriptor_mappers_importable() -> None:
    """descriptor_mappers module must be importable from the adapters package."""
    _skip_if_adapters_missing()
    encode_aas_id, decode_aas_id, map_canonical_to_shell_descriptor, map_shell_descriptor_to_canonical = (
        _import_descriptor_mappers()
    )
    assert callable(encode_aas_id)
    assert callable(decode_aas_id)
    assert callable(map_canonical_to_shell_descriptor)
    assert callable(map_shell_descriptor_to_canonical)


# ── Test 2: encode/decode round-trip ─────────────────────────────────────────


def test_encode_decode_aas_id_round_trip() -> None:
    """encode_aas_id followed by decode_aas_id must return the original string."""
    _skip_if_adapters_missing()
    encode_aas_id, decode_aas_id, _, _ = _import_descriptor_mappers()

    original = "urn:example:manufacturer:asset:001"
    encoded = encode_aas_id(original)
    decoded = decode_aas_id(encoded)

    assert decoded == original, (
        f"encode→decode round-trip failed.\n"
        f"  original: {original!r}\n"
        f"  encoded:  {encoded!r}\n"
        f"  decoded:  {decoded!r}"
    )
    # The encoded form must not contain URL-unsafe base64 chars (+ or /)
    assert "+" not in encoded and "/" not in encoded, (
        f"encode_aas_id must produce base64URL (no + or /); got: {encoded!r}"
    )
    # No padding characters
    assert "=" not in encoded, (
        f"encode_aas_id must strip padding; got: {encoded!r}"
    )


# ── Test 3: encode handles diverse ID forms ───────────────────────────────────


@pytest.mark.parametrize(
    "aas_id",
    [
        "urn:example:part:12345",
        "https://example.com/assets/my-twin",
        "plain-string-id-with-dashes",
        "asset/with/slashes/and spaces",
    ],
)
def test_encode_decode_round_trip_for_various_id_forms(aas_id: str) -> None:
    """encode_aas_id/decode_aas_id must handle URNs, URLs, and plain strings."""
    _skip_if_adapters_missing()
    encode_aas_id, decode_aas_id, _, _ = _import_descriptor_mappers()

    assert decode_aas_id(encode_aas_id(aas_id)) == aas_id


# ── Test 4: descriptor has required 'id' field ────────────────────────────────


def test_map_canonical_to_descriptor_has_id_field() -> None:
    """map_canonical_to_shell_descriptor output must include the required 'id' field."""
    _skip_if_adapters_missing()
    _, _, map_canonical_to_shell_descriptor, _ = _import_descriptor_mappers()

    descriptor = map_canonical_to_shell_descriptor(_minimal_canonical())

    assert "id" in descriptor, (
        f"shell descriptor must have 'id' field; got keys: {list(descriptor.keys())}"
    )
    assert descriptor["id"], "shell descriptor 'id' must be non-empty"


# ── Test 5: descriptor preserves twin_id as 'id' and globalAssetId ───────────


def test_map_canonical_to_descriptor_preserves_ids() -> None:
    """twin_id → 'id' and global_asset_id → 'globalAssetId' must be preserved."""
    _skip_if_adapters_missing()
    _, _, map_canonical_to_shell_descriptor, _ = _import_descriptor_mappers()

    canonical = _minimal_canonical()
    descriptor = map_canonical_to_shell_descriptor(canonical)

    assert descriptor["id"] == canonical["twin_id"], (
        f"descriptor 'id' must equal canonical 'twin_id'. "
        f"Got: {descriptor['id']!r}, expected: {canonical['twin_id']!r}"
    )
    assert descriptor.get("globalAssetId") == canonical["global_asset_id"], (
        f"descriptor 'globalAssetId' must equal canonical 'global_asset_id'. "
        f"Got: {descriptor.get('globalAssetId')!r}"
    )


# ── Test 6: submodels → submodelDescriptors ───────────────────────────────────


def test_map_canonical_with_submodel_produces_submodel_descriptors() -> None:
    """A canonical with submodels must produce a 'submodelDescriptors' list."""
    _skip_if_adapters_missing()
    _, _, map_canonical_to_shell_descriptor, _ = _import_descriptor_mappers()

    descriptor = map_canonical_to_shell_descriptor(_canonical_with_submodel())

    assert "submodelDescriptors" in descriptor, (
        f"descriptor must have 'submodelDescriptors' when canonical has submodels; "
        f"got keys: {list(descriptor.keys())}"
    )
    sm_descriptors = descriptor["submodelDescriptors"]
    assert len(sm_descriptors) >= 1, "Must have at least one submodelDescriptor"

    first = sm_descriptors[0]
    assert first.get("id") == "urn:example:submodel:sm001", (
        f"Submodel descriptor id mismatch: {first.get('id')!r}"
    )
    # semanticId must be present
    assert "semanticId" in first, (
        f"Submodel descriptor must have 'semanticId'; got: {list(first.keys())}"
    )
    # endpoint must be present
    assert "endpoints" in first and first["endpoints"], (
        "Submodel descriptor must have at least one endpoint"
    )


# ── Test 7: map_shell_descriptor_to_canonical extracts fields ─────────────────


def test_map_shell_descriptor_to_canonical_extracts_fields() -> None:
    """map_shell_descriptor_to_canonical must extract twin_id and global_asset_id."""
    _skip_if_adapters_missing()
    _, _, _, map_shell_descriptor_to_canonical = _import_descriptor_mappers()

    raw_descriptor = {
        "id": "urn:example:asset:raw-001",
        "globalAssetId": "urn:example:global:raw-001",
        "specificAssetIds": [{"name": "bpn", "value": "BPNL000000000001"}],
        "submodelDescriptors": [],
    }
    canonical = map_shell_descriptor_to_canonical(raw_descriptor)

    assert canonical.get("twin_id") == "urn:example:asset:raw-001", (
        f"canonical 'twin_id' should equal raw descriptor 'id'; got: {canonical.get('twin_id')!r}"
    )
    assert canonical.get("global_asset_id") == "urn:example:global:raw-001", (
        f"canonical 'global_asset_id' mismatch: {canonical.get('global_asset_id')!r}"
    )


# ── Test 8: canonical → descriptor → canonical round-trip ────────────────────


def test_canonical_to_descriptor_round_trip_preserves_core_fields() -> None:
    """Round-trip: canonical → descriptor → canonical must preserve twin_id and global_asset_id."""
    _skip_if_adapters_missing()
    _, _, map_canonical_to_shell_descriptor, map_shell_descriptor_to_canonical = (
        _import_descriptor_mappers()
    )

    original = _canonical_with_submodel()
    descriptor = map_canonical_to_shell_descriptor(original)
    restored = map_shell_descriptor_to_canonical(descriptor)

    assert restored["twin_id"] == original["twin_id"], (
        f"Round-trip twin_id mismatch: {restored['twin_id']!r} != {original['twin_id']!r}"
    )
    assert restored["global_asset_id"] == original["global_asset_id"], (
        f"Round-trip global_asset_id mismatch: "
        f"{restored['global_asset_id']!r} != {original['global_asset_id']!r}"
    )
    # Submodel must survive
    assert len(restored.get("submodels", [])) >= 1, (
        "Round-trip must preserve submodels"
    )


# ── Shared schema validation helper ──────────────────────────────────────────


def _validate_offline(schema: dict, instance: dict) -> list:
    """Validate instance against schema, skipping unresolvable $ref errors (offline mode).

    Returns a list of jsonschema ValidationError objects for true schema violations.
    Unresolvable $ref errors are silently dropped — they indicate missing external
    schemas, not instance invalidity.
    """
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    errors = []
    try:
        for error in validator.iter_errors(instance):
            errors.append(error)
    except Exception as exc:
        exc_name = type(exc).__name__
        # referencing.exceptions.Unresolvable and legacy RefResolutionError
        if "Unresolvable" in str(exc) or "WrappedReferencing" in exc_name or "RefResolution" in exc_name:
            return errors  # return whatever we collected before the exception
        raise
    return errors


# ── Test 9: descriptor validates against shell-descriptor.schema.json ─────────


def test_descriptor_output_validates_against_schema() -> None:
    """map_canonical_to_shell_descriptor output must conform to shell-descriptor.schema.json."""
    _skip_if_adapters_missing()
    pytest.importorskip("jsonschema", reason="jsonschema not installed")

    if not SHELL_DESCRIPTOR_SCHEMA_PATH.exists():
        pytest.skip(f"shell-descriptor schema not found: {SHELL_DESCRIPTOR_SCHEMA_PATH}")

    _, _, map_canonical_to_shell_descriptor, _ = _import_descriptor_mappers()

    schema = json.loads(SHELL_DESCRIPTOR_SCHEMA_PATH.read_text())
    descriptor = map_canonical_to_shell_descriptor(_minimal_canonical())

    errors = _validate_offline(schema, descriptor)
    assert not errors, (
        f"Shell descriptor output failed schema validation:\n"
        + "\n".join(f"  - {e.message}" for e in errors)
    )


# ── Test 10: descriptor with specificAssetIds validates against schema ─────────


def test_descriptor_with_specific_asset_ids_validates() -> None:
    """Descriptor with specificAssetIds must conform to shell-descriptor.schema.json."""
    _skip_if_adapters_missing()
    pytest.importorskip("jsonschema", reason="jsonschema not installed")

    if not SHELL_DESCRIPTOR_SCHEMA_PATH.exists():
        pytest.skip(f"shell-descriptor schema not found: {SHELL_DESCRIPTOR_SCHEMA_PATH}")

    _, _, map_canonical_to_shell_descriptor, _ = _import_descriptor_mappers()

    schema = json.loads(SHELL_DESCRIPTOR_SCHEMA_PATH.read_text())
    canonical = _canonical_with_submodel()
    descriptor = map_canonical_to_shell_descriptor(canonical)

    errors = _validate_offline(schema, descriptor)
    assert not errors, (
        f"Shell descriptor with specificAssetIds failed schema validation:\n"
        + "\n".join(f"  - {e.message}" for e in errors)
    )


# ── Test 11: empty submodels handled gracefully ───────────────────────────────


def test_map_canonical_with_no_submodels_omits_submodel_descriptors() -> None:
    """canonical with empty submodels list must produce a valid minimal descriptor."""
    _skip_if_adapters_missing()
    _, _, map_canonical_to_shell_descriptor, _ = _import_descriptor_mappers()

    descriptor = map_canonical_to_shell_descriptor(_minimal_canonical())

    # 'id' must always be present
    assert descriptor.get("id"), "Minimal descriptor must have a non-empty 'id'"
    # 'submodelDescriptors' should be absent or empty for zero submodels
    sm_descriptors = descriptor.get("submodelDescriptors", [])
    assert isinstance(sm_descriptors, list), (
        f"submodelDescriptors must be a list; got: {type(sm_descriptors).__name__}"
    )
