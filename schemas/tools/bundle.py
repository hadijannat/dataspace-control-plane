#!/usr/bin/env python3
"""
schemas/tools/bundle.py
Create offline compound JSON Schema bundles from registered source entrypoints.

Usage:
    python schemas/tools/bundle.py --entrypoint SCHEMA_PATH --out OUTPUT_PATH
    python schemas/tools/bundle.py --family FAMILY
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _support import (
    SCHEMAS_ROOT,
    artifact_id_from_relpath,
    build_local_schema_registry,
    bundle_relpath_for_source,
    collect_refs,
    def_key_for_path,
    dump_yaml,
    load_json,
    load_registry_catalog,
    provenance_relpath_for_artifact,
    relative_to_schemas,
    resolve_local_ref,
)


def _rewrite_document(
    document: Any,
    *,
    current_path: Path,
    root_defs: dict[str, Any],
    embedded: set[Path],
) -> Any:
    if isinstance(document, dict):
        rewritten: dict[str, Any] = {}
        for key, value in list(document.items()):
            if key == "$ref" and isinstance(value, str):
                if value.startswith("#"):
                    rewritten[key] = value
                    continue
                target_path, fragment = resolve_local_ref(value, current_path)
                if target_path is None:
                    rewritten[key] = value
                    continue
                if target_path == current_path.resolve() and fragment:
                    rewritten[key] = fragment
                    continue
                if not target_path.exists():
                    raise FileNotFoundError(f"Unresolved local ref '{value}' from {current_path}")
                def_key = def_key_for_path(target_path)
                if target_path not in embedded:
                    embedded.add(target_path)
                    target_schema = copy.deepcopy(load_json(target_path))
                    root_defs[def_key] = _rewrite_document(
                        target_schema,
                        current_path=target_path,
                        root_defs=root_defs,
                        embedded=embedded,
                    )
                if fragment.startswith("#/"):
                    rewritten[key] = f"#/$defs/{def_key}{fragment[1:]}"
                elif fragment in ("", "#"):
                    rewritten[key] = f"#/$defs/{def_key}"
                else:
                    rewritten[key] = f"#/$defs/{def_key}"
                continue
            rewritten[key] = _rewrite_document(
                value,
                current_path=current_path,
                root_defs=root_defs,
                embedded=embedded,
            )
        return rewritten

    if isinstance(document, list):
        return [
            _rewrite_document(item, current_path=current_path, root_defs=root_defs, embedded=embedded)
            for item in document
        ]

    return document


def build_bundle(entrypoint: Path, bundle_id: str | None = None) -> dict[str, Any]:
    entrypoint = entrypoint.resolve()
    root = copy.deepcopy(load_json(entrypoint))
    existing_defs = root.get("$defs", {})
    root["$defs"] = copy.deepcopy(existing_defs)
    embedded = {entrypoint}

    rewritten = _rewrite_document(
        root,
        current_path=entrypoint,
        root_defs=root["$defs"],
        embedded=embedded,
    )
    if bundle_id:
        rewritten["$id"] = bundle_id
    rewritten.setdefault("x-bundle-generated-at", datetime.now(tz=timezone.utc).isoformat())
    return rewritten


def _build_provenance(
    *,
    source_schema: dict[str, Any],
    source_entry: dict[str, Any],
    bundle_artifact_id: str,
) -> dict[str, Any]:
    return {
        "artifact_id": bundle_artifact_id,
        "local_version": source_entry["local_version"],
        "source_standard": source_schema.get("x-source-standard"),
        "source_standard_version": source_schema.get("x-source-version"),
        "source_uris": [source_entry["canonical_uri"]],
        "pack_dependencies": source_schema.get("x-pack-dependencies", []),
        "effective_date_range": {
            "from": source_entry["effective_from"],
            "to": source_entry.get("effective_to"),
        },
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "generator": "schemas/tools/bundle.py",
        "notes": "Compound offline bundle generated from a registered source entrypoint.",
    }


def _write_bundle(source_entry: dict[str, Any]) -> Path:
    source_rel = Path(source_entry["entrypoints"][0])
    source_path = (SCHEMAS_ROOT / source_rel).resolve()
    if "/source/" not in source_entry["entrypoints"][0]:
        raise ValueError(f"Refusing to bundle non-source entrypoint: {source_rel}")

    bundle_rel = bundle_relpath_for_source(source_rel)
    bundle_path = SCHEMAS_ROOT / bundle_rel
    bundle_id = f"https://dataspace-control-plane.internal/schemas/{bundle_rel.as_posix()}"
    bundle_doc = build_bundle(source_path, bundle_id=bundle_id)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(json.dumps(bundle_doc, indent=2) + "\n")

    provenance_rel = provenance_relpath_for_artifact(bundle_rel)
    provenance_path = SCHEMAS_ROOT / provenance_rel
    provenance = _build_provenance(
        source_schema=load_json(source_path),
        source_entry=source_entry,
        bundle_artifact_id=artifact_id_from_relpath(bundle_rel),
    )
    dump_yaml(provenance_path, provenance)
    return bundle_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--entrypoint", type=Path, help="Path to a source schema entrypoint.")
    group.add_argument("--family", help="Generate bundles for all source entrypoints in one family.")
    parser.add_argument("--out", type=Path, help="Output path for ad hoc bundling.")
    args = parser.parse_args(argv)

    if args.entrypoint:
        if not args.out:
            print("--out is required with --entrypoint", file=sys.stderr)
            return 2
        entrypoint = args.entrypoint.resolve()
        if not entrypoint.exists():
            print(f"Entrypoint not found: {entrypoint}", file=sys.stderr)
            return 1
        bundle_doc = build_bundle(entrypoint)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(bundle_doc, indent=2) + "\n")
        print(f"Bundle written: {args.out}")
        return 0

    catalog = load_registry_catalog()
    count = 0
    for entry in catalog.get("families", []):
        if entry["schema_family"] != args.family:
            continue
        primary = entry["entrypoints"][0]
        if "/source/" not in primary:
            continue
        out = _write_bundle(entry)
        print(f"Bundle written: {relative_to_schemas(out)}")
        count += 1

    print(f"{count} bundle(s) written for family '{args.family}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
