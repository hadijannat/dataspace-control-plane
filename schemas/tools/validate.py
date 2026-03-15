#!/usr/bin/env python3
"""
schemas/tools/validate.py
Validate every source JSON Schema against its declared meta-schema,
then run valid/invalid examples.

Usage:
    python schemas/tools/validate.py [--family FAMILY] [--fail-fast]

Exit codes:
    0  All schemas valid, all examples produce expected outcome.
    1  At least one failure.
    2  Usage error.

Requirements:
    pip install jsonschema pyyaml
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
    import jsonschema.validators
except ImportError:
    print("ERROR: jsonschema is required.  Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required.  Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent
DRAFT_2020_URI = "https://json-schema.org/draft/2020-12/schema"

# Families that contain local source JSON Schemas
FAMILIES = ["_shared", "vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping"]


def _load_json(path: Path) -> object:
    with open(path) as f:
        return json.load(f)


def _schema_meta_uri(schema: dict) -> str:
    return schema.get("$schema", DRAFT_2020_URI)


def _validate_schema_against_meta(schema_path: Path) -> list[str]:
    """Check that a schema document is itself valid JSON Schema."""
    errors = []
    try:
        schema = _load_json(schema_path)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"  PARSE ERROR {schema_path.relative_to(SCHEMAS_ROOT)}: {exc}"]

    meta_uri = _schema_meta_uri(schema)
    try:
        cls = jsonschema.validators.validator_for({"$schema": meta_uri})
        cls.check_schema(schema)
    except jsonschema.SchemaError as exc:
        errors.append(f"  SCHEMA ERROR {schema_path.relative_to(SCHEMAS_ROOT)}: {exc.message}")

    # Required top-level fields for local-authored schemas
    for field in ("$schema", "$id", "title", "description"):
        if field not in schema:
            errors.append(f"  MISSING FIELD {schema_path.relative_to(SCHEMAS_ROOT)}: '{field}' is required")

    return errors


def _run_examples(schema_path: Path) -> list[str]:
    """Run valid/ and invalid/ examples adjacent to the schema's source/ directory."""
    errors = []
    try:
        schema = _load_json(schema_path)
    except (json.JSONDecodeError, OSError):
        return []  # Already reported in validate_schema_against_meta

    # Locate examples directories relative to schema family root
    # e.g. schemas/vc/source/envelope/foo.schema.json → schemas/vc/examples/
    source_dir = schema_path
    while source_dir.name not in ("source", "derived") and source_dir != SCHEMAS_ROOT:
        source_dir = source_dir.parent
    family_dir = source_dir.parent

    examples_dir = family_dir / "examples"
    if not examples_dir.exists():
        return []

    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)

    for example_file in sorted((examples_dir / "valid").glob("*.json")):
        try:
            instance = _load_json(example_file)
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"  PARSE ERROR {example_file.relative_to(SCHEMAS_ROOT)}: {exc}")
            continue
        errs = list(validator.iter_errors(instance))
        if errs:
            for e in errs:
                errors.append(f"  INVALID (expected valid) {example_file.relative_to(SCHEMAS_ROOT)}: {e.message}")

    for example_file in sorted((examples_dir / "invalid").glob("*.json")):
        try:
            instance = _load_json(example_file)
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"  PARSE ERROR {example_file.relative_to(SCHEMAS_ROOT)}: {exc}")
            continue
        errs = list(validator.iter_errors(instance))
        if not errs:
            errors.append(f"  VALID (expected invalid) {example_file.relative_to(SCHEMAS_ROOT)}: should have failed")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--family", help="Limit to one schema family.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure.")
    args = parser.parse_args(argv)

    families = [args.family] if args.family else FAMILIES
    total_schemas = 0
    all_errors: list[str] = []

    for family in families:
        family_dir = SCHEMAS_ROOT / family
        if not family_dir.exists():
            continue

        schema_files = sorted(family_dir.rglob("source/**/*.schema.json"))
        schema_files += sorted(family_dir.rglob("_shared/**/*.schema.json"))
        schema_files += sorted((SCHEMAS_ROOT / "_shared").rglob("**/*.schema.json"))
        # Deduplicate
        seen: set[Path] = set()
        unique_files = []
        for sf in schema_files:
            if sf not in seen:
                seen.add(sf)
                unique_files.append(sf)

        for schema_path in unique_files:
            total_schemas += 1
            errs = _validate_schema_against_meta(schema_path)
            all_errors.extend(errs)
            if not errs:
                errs2 = _run_examples(schema_path)
                all_errors.extend(errs2)
            if args.fail_fast and all_errors:
                break

        if args.fail_fast and all_errors:
            break

    if all_errors:
        print(f"\n{len(all_errors)} error(s) across {total_schemas} schema(s):\n")
        for err in all_errors:
            print(err)
        return 1

    print(f"OK — {total_schemas} schema(s) validated, all examples pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
