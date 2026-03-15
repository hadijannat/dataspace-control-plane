#!/usr/bin/env python3
"""
schemas/tools/diff_schema.py
Compare two versions of a JSON Schema and classify changes as breaking or non-breaking.

Usage:
    python schemas/tools/diff_schema.py OLD_SCHEMA NEW_SCHEMA [--json]

Breaking changes (exit 1):
    - Required field added to an object (existing instances may be missing it)
    - Property type narrowed (e.g. string → integer)
    - Property removed from an object schema
    - Enum values removed
    - Pattern made more restrictive (detected as change, labelled breaking by convention)
    - minLength / minimum increased
    - maxLength / maximum decreased
    - additionalProperties changed from true/unset to false

Non-breaking changes (exit 0):
    - Required field removed (existing instances still validate)
    - New optional property added
    - Enum values added
    - Description or title changed
    - minLength / minimum decreased
    - maxLength / maximum increased

Output:
    Human-readable diff summary, or JSON with --json flag.

Exit codes:
    0  No breaking changes detected.
    1  Breaking changes detected.
    2  Usage error or parse failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _support import SCHEMAS_ROOT, load_registry_catalog


def _load(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _registered_entrypoints() -> set[Path]:
    catalog = load_registry_catalog()
    paths: set[Path] = set()
    for entry in catalog.get("families", []):
        for entrypoint in entry.get("entrypoints", []):
            path = (SCHEMAS_ROOT / entrypoint).resolve()
            if path.suffix == ".json":
                paths.add(path)
    return paths


def _ensure_registered(path: str, registered: set[Path]) -> None:
    candidate = Path(path).resolve()
    try:
        candidate.relative_to(SCHEMAS_ROOT)
    except ValueError:
        return
    if candidate not in registered:
        raise ValueError(f"{candidate} is not a registered schema entrypoint")


def _changes(old: Any, new: Any, path: str = "#") -> list[dict]:
    changes: list[dict] = []

    if type(old) != type(new):
        changes.append({"path": path, "kind": "type_change", "old": type(old).__name__, "new": type(new).__name__, "breaking": True})
        return changes

    if not isinstance(old, dict):
        if old != new:
            changes.append({"path": path, "kind": "value_change", "old": old, "new": new, "breaking": False})
        return changes

    # Required fields
    old_required = set(old.get("required", []))
    new_required = set(new.get("required", []))
    for field in new_required - old_required:
        changes.append({"path": f"{path}/required/{field}", "kind": "required_added", "field": field, "breaking": True})
    for field in old_required - new_required:
        changes.append({"path": f"{path}/required/{field}", "kind": "required_removed", "field": field, "breaking": False})

    # Properties
    old_props = old.get("properties", {})
    new_props = new.get("properties", {})
    for prop in set(old_props) - set(new_props):
        changes.append({"path": f"{path}/properties/{prop}", "kind": "property_removed", "breaking": True})
    for prop in set(new_props) - set(old_props):
        changes.append({"path": f"{path}/properties/{prop}", "kind": "property_added", "breaking": False})
    for prop in set(old_props) & set(new_props):
        changes.extend(_changes(old_props[prop], new_props[prop], f"{path}/properties/{prop}"))

    # Type narrowing
    old_type = old.get("type")
    new_type = new.get("type")
    if old_type != new_type and old_type is not None and new_type is not None:
        changes.append({"path": f"{path}/type", "kind": "type_narrowed", "old": old_type, "new": new_type, "breaking": True})

    # Enum
    old_enum = set(old.get("enum", []))
    new_enum = set(new.get("enum", []))
    if old_enum and old_enum != new_enum:
        removed = old_enum - new_enum
        added = new_enum - old_enum
        if removed:
            changes.append({"path": f"{path}/enum", "kind": "enum_values_removed", "removed": sorted(removed), "breaking": True})
        if added:
            changes.append({"path": f"{path}/enum", "kind": "enum_values_added", "added": sorted(added), "breaking": False})

    # Numeric bounds
    for bound, breaking_direction in [("minimum", "increase"), ("minLength", "increase"),
                                       ("maximum", "decrease"), ("maxLength", "decrease")]:
        ov = old.get(bound)
        nv = new.get(bound)
        if ov is not None and nv is not None and ov != nv:
            is_breaking = (breaking_direction == "increase" and nv > ov) or \
                          (breaking_direction == "decrease" and nv < ov)
            changes.append({"path": f"{path}/{bound}", "kind": f"{bound}_changed",
                             "old": ov, "new": nv, "breaking": is_breaking})

    # additionalProperties
    old_ap = old.get("additionalProperties")
    new_ap = new.get("additionalProperties")
    if old_ap != new_ap:
        breaking = new_ap is False and old_ap is not False
        changes.append({"path": f"{path}/additionalProperties", "kind": "additional_properties_changed",
                         "old": old_ap, "new": new_ap, "breaking": breaking})

    # Pattern (treat any change as potentially breaking)
    old_pat = old.get("pattern")
    new_pat = new.get("pattern")
    if old_pat != new_pat:
        changes.append({"path": f"{path}/pattern", "kind": "pattern_changed",
                         "old": old_pat, "new": new_pat, "breaking": True})

    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("old_schema", help="Path to the old schema version.")
    parser.add_argument("new_schema", help="Path to the new schema version.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON.")
    args = parser.parse_args(argv)

    try:
        registered = _registered_entrypoints()
        _ensure_registered(args.old_schema, registered)
        _ensure_registered(args.new_schema, registered)
        old = _load(args.old_schema)
        new = _load(args.new_schema)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    changes = _changes(old, new)
    breaking = [c for c in changes if c.get("breaking")]
    non_breaking = [c for c in changes if not c.get("breaking")]

    if args.as_json:
        print(json.dumps({
            "breaking": breaking,
            "non_breaking": non_breaking,
            "has_breaking_changes": bool(breaking),
        }, indent=2))
    else:
        if not changes:
            print("No schema changes detected.")
        else:
            if breaking:
                print(f"\n⚠  {len(breaking)} BREAKING change(s):")
                for c in breaking:
                    print(f"  {c['path']}: {c['kind']}")
            if non_breaking:
                print(f"\n✓  {len(non_breaking)} non-breaking change(s):")
                for c in non_breaking:
                    print(f"  {c['path']}: {c['kind']}")

    return 1 if breaking else 0


if __name__ == "__main__":
    sys.exit(main())
