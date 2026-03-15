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
