#!/usr/bin/env python3
"""
schemas/tools/validate.py
Validate the schemas contract registry offline:
1. meta-schemas
2. registry.yaml, family manifests, upstream lock
3. source and bundle schemas
4. per-artifact valid / invalid examples
5. provenance sidecars for published bundles
6. cross-family references through declared entrypoints only

Usage:
    python schemas/tools/validate.py [--family FAMILY] [--fail-fast]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import jsonschema

from _support import (
    FAMILIES,
    HOUSE_FIELDS,
    SCHEMAS_ROOT,
    build_local_schema_registry,
    collect_refs,
    is_internal_uri,
    load_json,
    load_registry_catalog,
    load_yaml,
    provenance_relpath_for_artifact,
    relative_to_schemas,
    resolve_local_ref,
)

REGISTRY_SCHEMA_PATH = SCHEMAS_ROOT / "_shared" / "meta" / "schema-catalog.schema.json"
MANIFEST_SCHEMA_PATH = SCHEMAS_ROOT / "_shared" / "meta" / "manifest.schema.json"
PROVENANCE_SCHEMA_PATH = SCHEMAS_ROOT / "_shared" / "meta" / "provenance.schema.json"
LOCK_FILE = SCHEMAS_ROOT / "locks" / "upstream.lock.yaml"

NON_SHARED_EXPECTED_DIRS = [
    "vendor",
    "source",
    "derived",
    "bundles",
    "examples/valid",
    "examples/invalid",
    "tests",
]
SHARED_EXPECTED_DIRS = ["meta", "vocab", "fragments", "tests", "derived/docs"]
LOCK_FORMATS = {"jsonld", "ttl", "json-schema", "yaml", "openapi", "xmi", "xsd", "pdf"}


def _validate_schema_document(schema_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        schema = load_json(schema_path)
    except Exception as exc:  # noqa: BLE001
        return [f"PARSE ERROR {relative_to_schemas(schema_path)}: {exc}"]

    try:
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
    except jsonschema.SchemaError as exc:
        errors.append(f"SCHEMA ERROR {relative_to_schemas(schema_path)}: {exc.message}")

    for field in HOUSE_FIELDS:
        if field not in schema:
            errors.append(f"MISSING FIELD {relative_to_schemas(schema_path)}: '{field}' is required")

    return errors


def _load_meta_schemas() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        load_json(REGISTRY_SCHEMA_PATH),
        load_json(MANIFEST_SCHEMA_PATH),
        load_json(PROVENANCE_SCHEMA_PATH),
    )


def _validate_registry_catalog(registry_schema: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    catalog = load_registry_catalog()
    try:
        jsonschema.Draft202012Validator(registry_schema).validate(catalog)
    except jsonschema.ValidationError as exc:
        errors.append(f"REGISTRY ERROR registry.yaml: {exc.message}")
    return errors, catalog


def _validate_manifests(manifest_schema: dict[str, Any], family_filter: str | None) -> list[str]:
    errors: list[str] = []
    families = [family_filter] if family_filter else [f for f in FAMILIES if f != "_shared"]
    validator = jsonschema.Draft202012Validator(manifest_schema)
    for family in families:
        manifest_path = SCHEMAS_ROOT / family / "manifest.yaml"
        if not manifest_path.exists():
            errors.append(f"MANIFEST ERROR {relative_to_schemas(manifest_path)}: missing file")
            continue
        manifest = load_yaml(manifest_path)
        try:
            validator.validate(manifest)
        except jsonschema.ValidationError as exc:
            errors.append(f"MANIFEST ERROR {relative_to_schemas(manifest_path)}: {exc.message}")
    return errors


def _validate_lock_file() -> list[str]:
    errors: list[str] = []
    if not LOCK_FILE.exists():
        return [f"LOCK ERROR {relative_to_schemas(LOCK_FILE)}: missing file"]

    lock = load_yaml(LOCK_FILE)
    if not isinstance(lock, dict):
        return [f"LOCK ERROR {relative_to_schemas(LOCK_FILE)}: root must be a mapping"]

    for key in ("lock_version", "generated_at", "upstream"):
        if key not in lock:
            errors.append(f"LOCK ERROR {relative_to_schemas(LOCK_FILE)}: missing '{key}'")

    upstream = lock.get("upstream", [])
    if not isinstance(upstream, list):
        errors.append(f"LOCK ERROR {relative_to_schemas(LOCK_FILE)}: 'upstream' must be a list")
        return errors

    seen_ids: set[str] = set()
    for entry in upstream:
        if not isinstance(entry, dict):
            errors.append("LOCK ERROR upstream entry must be a mapping")
            continue

        required = {
            "artifact_id", "family", "local_path", "source_uri", "standard", "version",
            "format", "retrieved_at", "sha256", "license",
        }
        missing = sorted(required - set(entry))
        if missing:
            errors.append(f"LOCK ERROR {entry.get('artifact_id', '<unknown>')}: missing {', '.join(missing)}")
            continue

        artifact_id = entry["artifact_id"]
        if artifact_id in seen_ids:
            errors.append(f"LOCK ERROR {artifact_id}: duplicate artifact_id")
        seen_ids.add(artifact_id)

        if entry["family"] not in FAMILIES or entry["family"] == "_shared":
            errors.append(f"LOCK ERROR {artifact_id}: invalid family '{entry['family']}'")

        if entry["format"] not in LOCK_FORMATS:
            errors.append(f"LOCK ERROR {artifact_id}: unsupported format '{entry['format']}'")

        if entry["sha256"] == "PENDING" or entry["retrieved_at"] == "PENDING":
            errors.append(f"LOCK ERROR {artifact_id}: unresolved pin metadata")
            continue

        local_path = SCHEMAS_ROOT / entry["local_path"]
        if not local_path.exists():
            errors.append(f"LOCK ERROR {artifact_id}: missing local artifact {entry['local_path']}")
            continue

        actual = local_path.read_bytes()
        actual_sha = __import__("hashlib").sha256(actual).hexdigest()
        if actual_sha != entry["sha256"]:
            errors.append(
                f"LOCK ERROR {artifact_id}: checksum mismatch expected {entry['sha256']} got {actual_sha}"
            )

    return errors


def _validate_family_directories(family_filter: str | None) -> list[str]:
    errors: list[str] = []
    families = [family_filter] if family_filter else FAMILIES
    for family in families:
        family_dir = SCHEMAS_ROOT / family
        if not family_dir.exists():
            errors.append(f"DIRECTORY ERROR {family}: missing family directory")
            continue
        expected = SHARED_EXPECTED_DIRS if family == "_shared" else NON_SHARED_EXPECTED_DIRS
        for rel in expected:
            path = family_dir / rel
            if not path.exists():
                errors.append(f"DIRECTORY ERROR {relative_to_schemas(path)}: missing directory")
    return errors


def _entrypoint_set(catalog: dict[str, Any]) -> set[Path]:
    paths: set[Path] = set()
    for entry in catalog.get("families", []):
        for item in entry.get("entrypoints", []):
            paths.add((SCHEMAS_ROOT / item).resolve())
    return paths


def _artifact_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["artifact_id"]: entry for entry in catalog.get("families", [])}


def _validate_catalog_coverage(catalog: dict[str, Any], family_filter: str | None) -> list[str]:
    errors: list[str] = []
    by_rel = {
        relative_to_schemas(Path(entry["entrypoints"][0]).resolve() if isinstance(entry["entrypoints"][0], Path) else (SCHEMAS_ROOT / entry["entrypoints"][0]).resolve()): entry
        for entry in catalog.get("families", [])
        if entry.get("entrypoints")
    }

    for schema_path in build_source_and_bundle_paths(family_filter):
        rel = relative_to_schemas(schema_path)
        if rel not in by_rel:
            errors.append(f"CATALOG ERROR registry.yaml: missing entry for {rel}")
            continue
        entry = by_rel[rel]
        schema = load_json(schema_path)
        if schema.get("$id") != entry["canonical_uri"]:
            errors.append(
                f"CATALOG ERROR {rel}: registry canonical_uri does not match $id"
            )

    return errors


def build_source_and_bundle_paths(family_filter: str | None) -> list[Path]:
    paths: list[Path] = []
    families = [family_filter] if family_filter else FAMILIES
    for family in families:
        family_dir = SCHEMAS_ROOT / family
        if not family_dir.exists():
            continue
        if family == "_shared":
            paths.extend(sorted((family_dir / "meta").glob("*.schema.json")))
            continue
        source_dir = family_dir / "source"
        bundle_dir = family_dir / "bundles"
        if source_dir.exists():
            paths.extend(sorted(source_dir.rglob("*.schema.json")))
        if bundle_dir.exists():
            paths.extend(sorted(bundle_dir.glob("*.schema.json")))
    return paths


def _validate_schema_files(family_filter: str | None) -> list[str]:
    errors: list[str] = []
    for schema_path in build_source_and_bundle_paths(family_filter):
        errors.extend(_validate_schema_document(schema_path))
    return errors


def _example_dirs_for_artifact(family: str, artifact_id: str) -> tuple[Path, Path]:
    family_dir = SCHEMAS_ROOT / family / "examples"
    return family_dir / "valid" / artifact_id, family_dir / "invalid" / artifact_id


def _validate_examples(catalog: dict[str, Any], family_filter: str | None) -> list[str]:
    errors: list[str] = []
    registry = build_local_schema_registry(include_bundles=True)

    for entry in catalog.get("families", []):
        family = entry["schema_family"]
        if family == "_shared":
            continue
        if family_filter and family != family_filter:
            continue

        primary = entry["entrypoints"][0]
        if "/bundles/" in primary:
            continue
        schema_path = (SCHEMAS_ROOT / primary).resolve()
        if not schema_path.exists():
            continue

        schema = load_json(schema_path)
        validator = jsonschema.Draft202012Validator(schema, registry=registry)
        valid_dir, invalid_dir = _example_dirs_for_artifact(family, entry["artifact_id"])
        valid_files = sorted(valid_dir.glob("*.json")) if valid_dir.exists() else []
        invalid_files = sorted(invalid_dir.glob("*.json")) if invalid_dir.exists() else []
        if not valid_files and not invalid_files:
            continue

        for example_path in valid_files:
            instance = load_json(example_path)
            example_errors = list(validator.iter_errors(instance))
            if example_errors:
                for exc in example_errors:
                    errors.append(f"EXAMPLE ERROR {relative_to_schemas(example_path)}: expected valid, got {exc.message}")

        for example_path in invalid_files:
            instance = load_json(example_path)
            example_errors = list(validator.iter_errors(instance))
            if not example_errors:
                errors.append(f"EXAMPLE ERROR {relative_to_schemas(example_path)}: expected invalid, got valid")

    return errors


def _validate_bundle_provenance(catalog: dict[str, Any], provenance_schema: dict[str, Any], family_filter: str | None) -> list[str]:
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(provenance_schema)
    for entry in catalog.get("families", []):
        family = entry["schema_family"]
        if family == "_shared":
            continue
        if family_filter and family != family_filter:
            continue
        primary = entry["entrypoints"][0]
        if "/bundles/" not in primary:
            continue
        artifact_path = (SCHEMAS_ROOT / primary).resolve()
        provenance_path = provenance_relpath_for_artifact(relative_to_schemas(artifact_path))
        provenance_abs = SCHEMAS_ROOT / provenance_path
        if not provenance_abs.exists():
            errors.append(f"PROVENANCE ERROR {provenance_path}: missing sidecar")
            continue
        data = load_yaml(provenance_abs)
        try:
            validator.validate(data)
        except jsonschema.ValidationError as exc:
            errors.append(f"PROVENANCE ERROR {provenance_path}: {exc.message}")
    return errors


def _validate_cross_family_refs(catalog: dict[str, Any], family_filter: str | None) -> list[str]:
    errors: list[str] = []
    entrypoints = _entrypoint_set(catalog)
    families = [family_filter] if family_filter else [f for f in FAMILIES if f != "_shared"]
    for family in families:
        for schema_path in sorted((SCHEMAS_ROOT / family / "source").rglob("*.schema.json")):
            refs = collect_refs(load_json(schema_path))
            for ref in refs:
                if ref.startswith("#"):
                    continue
                if not is_internal_uri(ref):
                    continue
                target_path, _fragment = resolve_local_ref(ref, schema_path)
                if target_path is None or not target_path.exists():
                    errors.append(f"REF ERROR {relative_to_schemas(schema_path)}: unresolved ref {ref}")
                    continue
                if relative_to_schemas(target_path).parts[0] == family:
                    continue
                if target_path not in entrypoints:
                    errors.append(
                        f"REF ERROR {relative_to_schemas(schema_path)}: cross-family ref {ref} does not target a declared entrypoint"
                    )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", help="Limit family-local checks to one schema family.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop after the first error.")
    args = parser.parse_args(argv)

    registry_schema, manifest_schema, provenance_schema = _load_meta_schemas()
    all_errors: list[str] = []

    def extend(errors: list[str]) -> None:
        all_errors.extend(errors)
        if args.fail_fast and all_errors:
            raise SystemExit(1)

    extend(_validate_family_directories(args.family))
    extend(_validate_schema_files(args.family))
    registry_errors, catalog = _validate_registry_catalog(registry_schema)
    extend(registry_errors)
    extend(_validate_manifests(manifest_schema, args.family))
    extend(_validate_lock_file())
    extend(_validate_catalog_coverage(catalog, args.family))
    extend(_validate_cross_family_refs(catalog, args.family))
    extend(_validate_examples(catalog, args.family))
    extend(_validate_bundle_provenance(catalog, provenance_schema, args.family))

    if all_errors:
        print(f"\n{len(all_errors)} validation error(s):\n")
        for error in all_errors:
            print(error)
        return 1

    print("OK — registry, manifests, lock file, schemas, examples, provenance, and cross-family refs validated offline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
