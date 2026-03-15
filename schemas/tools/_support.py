from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import referencing
import yaml

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SCHEMAS_ROOT.parent
INTERNAL_BASE = "https://dataspace-control-plane.internal/schemas/"
FAMILIES = ["_shared", "vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping"]
HOUSE_FIELDS = ("$schema", "$id", "title", "description", "x-source-standard", "x-source-version", "x-pack-dependencies")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def dump_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative_to_schemas(path: Path) -> Path:
    return path.resolve().relative_to(SCHEMAS_ROOT)


def is_internal_uri(uri: str) -> bool:
    return uri.startswith(INTERNAL_BASE)


def split_ref(ref: str) -> tuple[str, str]:
    if "#" in ref:
        base, fragment = ref.split("#", 1)
        return base, f"#{fragment}"
    return ref, ""


def resolve_local_ref(ref: str, current_path: Path) -> tuple[Path | None, str]:
    base_ref, fragment = split_ref(ref)
    if ref.startswith("#"):
        return current_path.resolve(), fragment or ref

    if is_internal_uri(base_ref):
        rel = base_ref[len(INTERNAL_BASE):]
        return (SCHEMAS_ROOT / rel).resolve(), fragment

    parsed = urlparse(base_ref)
    if parsed.scheme:
        return None, fragment

    if not base_ref:
        return current_path.resolve(), fragment

    return (current_path.parent / base_ref).resolve(), fragment


def def_key_for_path(path: Path) -> str:
    rel = relative_to_schemas(path)
    return str(rel).replace("/", "__").replace(".", "_").replace("-", "_")


def iter_schema_paths(*, include_bundles: bool = False) -> list[Path]:
    paths: list[Path] = []
    for family in FAMILIES:
        family_dir = SCHEMAS_ROOT / family
        if not family_dir.exists():
            continue
        if family == "_shared":
            paths.extend(sorted((family_dir / "meta").glob("*.schema.json")))
            continue
        source_dir = family_dir / "source"
        if source_dir.exists():
            paths.extend(sorted(source_dir.rglob("*.schema.json")))
        if include_bundles:
            bundle_dir = family_dir / "bundles"
            if bundle_dir.exists():
                paths.extend(sorted(bundle_dir.glob("*.schema.json")))
    return paths


def build_local_schema_registry(*, include_bundles: bool = False) -> referencing.Registry:
    resources: list[tuple[str, referencing.Resource[Any]]] = []
    for schema_path in iter_schema_paths(include_bundles=include_bundles):
        schema = load_json(schema_path)
        schema_id = schema.get("$id")
        if schema_id:
            resources.append((schema_id, referencing.Resource.from_contents(schema)))
    return referencing.Registry().with_resources(resources)


def collect_refs(document: Any, refs: set[str] | None = None) -> set[str]:
    if refs is None:
        refs = set()
    if isinstance(document, dict):
        ref = document.get("$ref")
        if isinstance(ref, str):
            refs.add(ref)
        for value in document.values():
            collect_refs(value, refs)
    elif isinstance(document, list):
        for value in document:
            collect_refs(value, refs)
    return refs


def artifact_id_from_relpath(rel_path: Path) -> str:
    family = rel_path.parts[0]
    name = rel_path.name
    if name.endswith(".bundle.schema.json"):
        base = name.removesuffix(".bundle.schema.json")
        return f"{family}.{base}.bundle"
    if name.endswith(".schema.json"):
        base = name.removesuffix(".schema.json")
        if family == "_shared" and len(rel_path.parts) > 1 and rel_path.parts[1] == "meta":
            return f"meta.{base}"
        return f"{family}.{base}"
    raise ValueError(f"Unsupported artifact path: {rel_path}")


def bundle_relpath_for_source(source_rel: Path) -> Path:
    family = source_rel.parts[0]
    name = source_rel.name.removesuffix(".schema.json")
    return Path(family) / "bundles" / f"{name}.bundle.schema.json"


def provenance_relpath_for_artifact(artifact_rel: Path) -> Path:
    name = artifact_rel.name
    if name.endswith(".schema.json"):
        return artifact_rel.with_name(name.removesuffix(".schema.json") + ".provenance.yaml")
    return artifact_rel.with_suffix(artifact_rel.suffix + ".provenance.yaml")


def load_registry_catalog() -> dict[str, Any]:
    return load_yaml(SCHEMAS_ROOT / "registry.yaml")

