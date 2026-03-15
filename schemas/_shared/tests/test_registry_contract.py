from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = SCHEMAS_ROOT / "registry.yaml"
REGISTRY_SCHEMA_PATH = SCHEMAS_ROOT / "_shared" / "meta" / "schema-catalog.schema.json"
MANIFEST_SCHEMA_PATH = SCHEMAS_ROOT / "_shared" / "meta" / "manifest.schema.json"
PROVENANCE_SCHEMA_PATH = SCHEMAS_ROOT / "_shared" / "meta" / "provenance.schema.json"
LOCK_PATH = SCHEMAS_ROOT / "locks" / "upstream.lock.yaml"
INTERNAL_BASE = "https://dataspace-control-plane.internal/schemas/"
FAMILIES = ["vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping"]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _bundle_refs(document) -> list[str]:
    refs: list[str] = []
    if isinstance(document, dict):
        ref = document.get("$ref")
        if isinstance(ref, str):
            refs.append(ref)
        for value in document.values():
            refs.extend(_bundle_refs(value))
    elif isinstance(document, list):
        for value in document:
            refs.extend(_bundle_refs(value))
    return refs


def test_registry_validates_against_meta_schema() -> None:
    validator = jsonschema.Draft202012Validator(_load_json(REGISTRY_SCHEMA_PATH))
    validator.validate(_load_yaml(REGISTRY_PATH))


def test_manifests_validate_against_manifest_schema() -> None:
    validator = jsonschema.Draft202012Validator(_load_json(MANIFEST_SCHEMA_PATH))
    for family in FAMILIES:
        validator.validate(_load_yaml(SCHEMAS_ROOT / family / "manifest.yaml"))


def test_lock_file_has_no_pending_entries() -> None:
    lock = _load_yaml(LOCK_PATH)
    for entry in lock["upstream"]:
        assert entry["sha256"] != "PENDING"
        assert entry["retrieved_at"] != "PENDING"
        assert (SCHEMAS_ROOT / entry["local_path"]).exists()


def test_bundle_provenance_sidecars_validate() -> None:
    validator = jsonschema.Draft202012Validator(_load_json(PROVENANCE_SCHEMA_PATH))
    for family in FAMILIES:
        for sidecar in sorted((SCHEMAS_ROOT / family / "bundles").glob("*.provenance.yaml")):
            validator.validate(_load_yaml(sidecar))


def test_bundle_refs_do_not_leak_internal_source_uris() -> None:
    for family in FAMILIES:
        for bundle in sorted((SCHEMAS_ROOT / family / "bundles").glob("*.schema.json")):
            refs = _bundle_refs(_load_json(bundle))
            leaked = [ref for ref in refs if ref.startswith(INTERNAL_BASE)]
            assert not leaked, f"{bundle.name} leaked internal source refs: {leaked}"


def test_registry_covers_all_source_and_bundle_schema_files() -> None:
    registry = _load_yaml(REGISTRY_PATH)
    registered = {
        entrypoint
        for entry in registry["families"]
        for entrypoint in entry["entrypoints"]
    }
    actual = set()
    actual.update(str(path.relative_to(SCHEMAS_ROOT)) for path in (SCHEMAS_ROOT / "_shared" / "meta").glob("*.schema.json"))
    for family in FAMILIES:
        actual.update(str(path.relative_to(SCHEMAS_ROOT)) for path in (SCHEMAS_ROOT / family / "source").rglob("*.schema.json"))
        actual.update(str(path.relative_to(SCHEMAS_ROOT)) for path in (SCHEMAS_ROOT / family / "bundles").glob("*.schema.json"))
    assert actual == registered


# ---------------------------------------------------------------------------
# Additional contract tests
# ---------------------------------------------------------------------------

def test_lock_sha256_entries_are_valid_hex_strings() -> None:
    """Every sha256 value in upstream.lock.yaml must be a 64-character lowercase hex string."""
    lock = _load_yaml(LOCK_PATH)
    import re
    hex_re = re.compile(r"^[0-9a-f]{64}$")
    for entry in lock["upstream"]:
        sha = entry.get("sha256", "")
        assert sha != "PENDING", f"Unresolved PENDING sha256 for {entry.get('local_path')}"
        assert hex_re.match(sha), (
            f"sha256 for {entry.get('local_path')!r} is not 64 lowercase hex chars: {sha!r}"
        )


def test_bundles_do_not_cross_family_source_boundaries() -> None:
    """A bundle in family A must not $ref the source/ directory of family B."""
    for family in FAMILIES:
        bundle_dir = SCHEMAS_ROOT / family / "bundles"
        if not bundle_dir.exists():
            continue
        for bundle_path in bundle_dir.glob("*.schema.json"):
            refs = _bundle_refs(_load_json(bundle_path))
            for ref in refs:
                for other_family in FAMILIES:
                    if other_family == family:
                        continue
                    cross_source_prefix = f"{INTERNAL_BASE}{other_family}/source/"
                    assert not ref.startswith(cross_source_prefix), (
                        f"{bundle_path.name} in '{family}' cross-references source of "
                        f"'{other_family}': {ref}"
                    )


def test_vc_credential_envelope_has_required_fields() -> None:
    """Regression anchor: credential-envelope.schema.json must keep its contract fields."""
    schema_path = (
        SCHEMAS_ROOT / "vc" / "source" / "envelope" / "credential-envelope.schema.json"
    )
    if not schema_path.exists():
        pytest.skip("credential-envelope.schema.json not present")
    schema = _load_json(schema_path)
    required = set(schema.get("required", []))
    for field in ("@context", "type", "credentialSubject"):
        assert field in required or field in schema.get("properties", {}), (
            f"VC credential-envelope missing mandatory field '{field}'"
        )


def test_dpp_passport_envelope_has_required_fields() -> None:
    """Regression anchor: passport-envelope.schema.json must keep its contract fields.

    DPP is IDTA-based (not JSON-LD), so there is no @context requirement.
    The core contract fields are passportId, subject, and lifecycle.
    """
    schema_path = (
        SCHEMAS_ROOT / "dpp" / "source" / "base" / "passport-envelope.schema.json"
    )
    if not schema_path.exists():
        pytest.skip("passport-envelope.schema.json not present")
    schema = _load_json(schema_path)
    required = set(schema.get("required", []))
    props = set(schema.get("properties", {}).keys())
    assert required or props, "passport-envelope schema has no required fields or properties"
    for field in ("passportId", "subject", "lifecycle"):
        assert field in required or field in props, (
            f"DPP passport-envelope missing mandatory contract field '{field}'"
        )


def test_provenance_sidecars_have_non_empty_required_fields() -> None:
    """All provenance sidecar fields required by the schema must be non-empty strings."""
    provenance_schema = _load_json(PROVENANCE_SCHEMA_PATH)
    required_fields = provenance_schema.get("required", [])
    for family in FAMILIES:
        bundle_dir = SCHEMAS_ROOT / family / "bundles"
        if not bundle_dir.exists():
            continue
        for sidecar in sorted(bundle_dir.glob("*.provenance.yaml")):
            data = _load_yaml(sidecar)
            for field in required_fields:
                value = data.get(field)
                assert value is not None, (
                    f"{sidecar.name}: required provenance field '{field}' is missing"
                )
                if isinstance(value, str):
                    assert value.strip(), (
                        f"{sidecar.name}: required provenance field '{field}' is empty"
                    )
