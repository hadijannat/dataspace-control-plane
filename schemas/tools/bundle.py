#!/usr/bin/env python3
"""
schemas/tools/bundle.py
Create compound JSON Schema bundle documents using $defs.

Per JSON Schema 2020-12 compound schema document semantics: each embedded schema
resource may declare its own $schema value; validation happens per schema resource,
not by naively applying one meta-schema to the whole bundle.

Usage:
    python schemas/tools/bundle.py --entrypoint SCHEMA_PATH --out OUTPUT_PATH
    python schemas/tools/bundle.py --family FAMILY  # bundle all entrypoints for a family

Output: a single JSON file with all referenced local schemas embedded in $defs.
External URIs (http/https) are left as $ref strings — callers must resolve them
against vendor/ artifacts or a local resolver.

Exit codes:
    0  Bundle written successfully.
    1  Error during bundling.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required.  Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent
INTERNAL_BASE = "https://dataspace-control-plane.internal/schemas/"


def _is_local_ref(ref: str) -> bool:
    """True if $ref resolves to a local schema (our internal base URI)."""
    return ref.startswith(INTERNAL_BASE) or ref.startswith("#/") or not urlparse(ref).scheme


def _id_to_path(schema_id: str) -> Path | None:
    """Convert an internal $id to a file path relative to SCHEMAS_ROOT."""
    if schema_id.startswith(INTERNAL_BASE):
        rel = schema_id[len(INTERNAL_BASE):]
        return SCHEMAS_ROOT / rel
    return None


def _collect_refs(schema: dict | list | str | int | float | bool | None,
                  refs: set[str]) -> None:
    if isinstance(schema, dict):
        if "$ref" in schema and isinstance(schema["$ref"], str):
            refs.add(schema["$ref"])
        for v in schema.values():
            _collect_refs(v, refs)
    elif isinstance(schema, list):
        for item in schema:
            _collect_refs(item, refs)


def _load_schema(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def bundle(entrypoint: Path, *, visited: dict[str, dict] | None = None) -> dict:
    """Recursively collect all local $refs into $defs of the root schema."""
    if visited is None:
        visited = {}

    root = _load_schema(entrypoint)
    root_id = root.get("$id", str(entrypoint))

    if root_id in visited:
        return visited[root_id]

    visited[root_id] = root

    refs: set[str] = set()
    _collect_refs(root, refs)

    defs = root.setdefault("$defs", {})

    for ref in refs:
        if not _is_local_ref(ref):
            continue  # External ref — leave as-is

        # Resolve to a file path
        ref_path = _id_to_path(ref)
        if ref_path is None:
            # Relative ref — resolve against entrypoint's directory
            ref_path = entrypoint.parent / ref

        ref_path = ref_path.resolve()
        if not ref_path.exists():
            print(f"  WARNING: $ref target not found: {ref_path}", file=sys.stderr)
            continue

        if str(ref_path) in {str(k) for k in visited}:
            continue

        embedded = bundle(ref_path, visited=visited)
        # Use a safe key derived from the $id
        def_key = ref.replace(INTERNAL_BASE, "").replace("/", "__").replace(".", "_")
        defs[def_key] = embedded

    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--entrypoint", type=Path, help="Path to the root schema to bundle.")
    group.add_argument("--family", help="Bundle all registry entrypoints for a family.")
    parser.add_argument("--out", type=Path, help="Output path (required with --entrypoint).")
    args = parser.parse_args(argv)

    if args.entrypoint:
        if not args.out:
            print("--out is required when --entrypoint is used.", file=sys.stderr)
            return 2
        ep = args.entrypoint.resolve()
        if not ep.exists():
            print(f"Entrypoint not found: {ep}", file=sys.stderr)
            return 1
        bundle_doc = bundle(ep)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(bundle_doc, indent=2))
        print(f"Bundle written: {args.out}")
        return 0

    if args.family:
        # Load registry and find entrypoints for this family
        registry_path = SCHEMAS_ROOT / "registry.yaml"
        with open(registry_path) as f:
            reg = yaml.safe_load(f)

        count = 0
        for entry in reg.get("families", []):
            if entry.get("schema_family") != args.family:
                continue
            for ep_rel in entry.get("entrypoints", []):
                ep = SCHEMAS_ROOT / ep_rel
                if not ep.exists() or not ep_rel.endswith(".schema.json"):
                    continue
                out = SCHEMAS_ROOT / args.family / "bundles" / Path(ep_rel).name
                bundle_doc = bundle(ep)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(bundle_doc, indent=2))
                print(f"  Bundle written: {out.relative_to(SCHEMAS_ROOT)}")
                count += 1

        print(f"\n{count} bundle(s) written for family '{args.family}'.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
