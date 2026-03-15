"""
schemas/tools/tests/test_support_unit.py
Unit tests for pure-function helpers in schemas/tools/_support.py
and the core bundling logic in schemas/tools/bundle.py.

conftest.py in this directory inserts schemas/tools/ into sys.path.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from _support import (
    INTERNAL_BASE,
    SCHEMAS_ROOT,
    artifact_id_from_relpath,
    bundle_relpath_for_source,
    collect_refs,
    def_key_for_path,
    is_internal_uri,
    provenance_relpath_for_artifact,
    resolve_local_ref,
    sha256_bytes,
    split_ref,
)


# ---------------------------------------------------------------------------
# sha256_bytes
# ---------------------------------------------------------------------------

def test_sha256_bytes_returns_64_hex_chars() -> None:
    digest = sha256_bytes(b"hello")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_sha256_bytes_is_deterministic() -> None:
    payload = b"dataspace-control-plane"
    assert sha256_bytes(payload) == sha256_bytes(payload)


def test_sha256_bytes_matches_stdlib() -> None:
    payload = b"test-payload"
    expected = hashlib.sha256(payload).hexdigest()
    assert sha256_bytes(payload) == expected


# ---------------------------------------------------------------------------
# split_ref
# ---------------------------------------------------------------------------

def test_split_ref_with_fragment() -> None:
    base, frag = split_ref("foo.schema.json#/definitions/bar")
    assert base == "foo.schema.json"
    assert frag == "#/definitions/bar"


def test_split_ref_without_fragment() -> None:
    base, frag = split_ref("foo.schema.json")
    assert base == "foo.schema.json"
    assert frag == ""


def test_split_ref_hash_prefix_only() -> None:
    base, frag = split_ref("#/definitions/bar")
    assert base == ""
    assert frag == "#/definitions/bar"


def test_split_ref_bare_hash() -> None:
    base, frag = split_ref("#")
    assert base == ""
    assert frag == "#"


# ---------------------------------------------------------------------------
# is_internal_uri
# ---------------------------------------------------------------------------

def test_is_internal_uri_true() -> None:
    assert is_internal_uri(
        f"{INTERNAL_BASE}vc/source/envelope/credential-envelope.schema.json"
    )


def test_is_internal_uri_false_for_external_w3c() -> None:
    assert not is_internal_uri("https://www.w3.org/ns/credentials/v2")


def test_is_internal_uri_false_for_relative_path() -> None:
    assert not is_internal_uri("../foo.schema.json")


def test_is_internal_uri_false_for_empty_string() -> None:
    assert not is_internal_uri("")


# ---------------------------------------------------------------------------
# resolve_local_ref
# ---------------------------------------------------------------------------

def test_resolve_local_ref_hash_returns_current_path(tmp_path: Path) -> None:
    current = tmp_path / "foo.schema.json"
    current.write_text("{}")
    target, frag = resolve_local_ref("#/$defs/Bar", current)
    assert target == current.resolve()
    assert frag == "#/$defs/Bar"


def test_resolve_local_ref_external_uri_returns_none(tmp_path: Path) -> None:
    current = tmp_path / "foo.schema.json"
    current.write_text("{}")
    target, _ = resolve_local_ref("https://www.w3.org/ns/credentials/v2", current)
    assert target is None


def test_resolve_local_ref_internal_uri_maps_to_schemas_root(tmp_path: Path) -> None:
    current = tmp_path / "foo.schema.json"
    current.write_text("{}")
    rel = "vc/source/envelope/credential-envelope.schema.json"
    target, frag = resolve_local_ref(f"{INTERNAL_BASE}{rel}", current)
    assert target == (SCHEMAS_ROOT / rel).resolve()
    assert frag == ""


def test_resolve_local_ref_internal_uri_with_fragment(tmp_path: Path) -> None:
    current = tmp_path / "foo.schema.json"
    current.write_text("{}")
    rel = "vc/source/envelope/credential-envelope.schema.json"
    target, frag = resolve_local_ref(f"{INTERNAL_BASE}{rel}#/$defs/issuer", current)
    assert target == (SCHEMAS_ROOT / rel).resolve()
    assert frag == "#/$defs/issuer"


def test_resolve_local_ref_relative_resolves_against_parent(tmp_path: Path) -> None:
    current = tmp_path / "subdir" / "foo.schema.json"
    current.parent.mkdir()
    current.write_text("{}")
    target, frag = resolve_local_ref("bar.schema.json", current)
    assert target == (tmp_path / "subdir" / "bar.schema.json").resolve()
    assert frag == ""


# ---------------------------------------------------------------------------
# def_key_for_path
# ---------------------------------------------------------------------------

def test_def_key_for_path_replaces_slashes_dots_and_hyphens() -> None:
    path = SCHEMAS_ROOT / "vc" / "source" / "envelope" / "credential-envelope.schema.json"
    key = def_key_for_path(path)
    assert "/" not in key
    assert "." not in key
    assert "-" not in key
    assert key == "vc__source__envelope__credential_envelope_schema_json"


# ---------------------------------------------------------------------------
# artifact_id_from_relpath
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel,expected", [
    ("vc/source/envelope/credential-envelope.schema.json", "vc.credential-envelope"),
    ("dpp/bundles/passport-envelope.bundle.schema.json", "dpp.passport-envelope.bundle"),
    ("_shared/meta/manifest.schema.json", "meta.manifest"),
    ("metering/source/business/usage-record.schema.json", "metering.usage-record"),
    ("aas/source/profiles/shell.schema.json", "aas.shell"),
])
def test_artifact_id_from_relpath(rel: str, expected: str) -> None:
    assert artifact_id_from_relpath(Path(rel)) == expected


# ---------------------------------------------------------------------------
# bundle_relpath_for_source
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("src,expected_bundle", [
    (
        "vc/source/envelope/credential-envelope.schema.json",
        "vc/bundles/credential-envelope.bundle.schema.json",
    ),
    (
        "dpp/source/base/passport-envelope.schema.json",
        "dpp/bundles/passport-envelope.bundle.schema.json",
    ),
    (
        "metering/source/business/usage-record.schema.json",
        "metering/bundles/usage-record.bundle.schema.json",
    ),
])
def test_bundle_relpath_for_source(src: str, expected_bundle: str) -> None:
    result = bundle_relpath_for_source(Path(src))
    assert result == Path(expected_bundle)


# ---------------------------------------------------------------------------
# provenance_relpath_for_artifact
# ---------------------------------------------------------------------------

def test_provenance_relpath_for_bundle_schema() -> None:
    result = provenance_relpath_for_artifact(
        Path("vc/bundles/credential-envelope.bundle.schema.json")
    )
    assert result == Path("vc/bundles/credential-envelope.bundle.provenance.yaml")


def test_provenance_relpath_for_source_schema() -> None:
    result = provenance_relpath_for_artifact(
        Path("vc/source/envelope/credential-envelope.schema.json")
    )
    assert result == Path("vc/source/envelope/credential-envelope.provenance.yaml")


# ---------------------------------------------------------------------------
# collect_refs
# ---------------------------------------------------------------------------

def test_collect_refs_finds_nested_refs() -> None:
    doc = {
        "$ref": "A",
        "properties": {
            "x": {"$ref": "B"},
            "y": {"items": {"$ref": "C"}},
        },
    }
    assert collect_refs(doc) == {"A", "B", "C"}


def test_collect_refs_ignores_non_ref_keys() -> None:
    doc = {"type": "object", "title": "Foo", "description": "Bar"}
    assert collect_refs(doc) == set()


def test_collect_refs_handles_list_of_schemas() -> None:
    doc = [{"$ref": "X"}, {"$ref": "Y"}, {"type": "string"}]
    assert collect_refs(doc) == {"X", "Y"}


def test_collect_refs_empty_document() -> None:
    assert collect_refs({}) == set()
    assert collect_refs([]) == set()


def test_collect_refs_does_not_collect_non_string_refs() -> None:
    doc = {"$ref": 42, "properties": {"x": {"type": "string"}}}
    assert collect_refs(doc) == set()


# ---------------------------------------------------------------------------
# build_bundle integration (uses real schema files from SCHEMAS_ROOT)
# ---------------------------------------------------------------------------

def test_build_bundle_inlines_refs_and_removes_internal_uris() -> None:
    """build_bundle must not leave any internal source $ref values in the output."""
    from bundle import build_bundle  # noqa: PLC0415

    entrypoint = (
        SCHEMAS_ROOT / "vc" / "source" / "envelope" / "credential-envelope.schema.json"
    )
    bundle = build_bundle(entrypoint)
    leaked = [
        ref for ref in collect_refs(bundle)
        if isinstance(ref, str) and ref.startswith(INTERNAL_BASE)
    ]
    assert not leaked, f"Bundle leaked internal source refs: {leaked}"


def test_build_bundle_overrides_dollar_id_when_bundle_id_given() -> None:
    from bundle import build_bundle  # noqa: PLC0415

    entrypoint = (
        SCHEMAS_ROOT / "vc" / "source" / "envelope" / "credential-envelope.schema.json"
    )
    custom_id = "https://example.com/test-bundle.schema.json"
    bundle = build_bundle(entrypoint, bundle_id=custom_id)
    assert bundle["$id"] == custom_id


def test_build_bundle_stamps_generated_at_timestamp() -> None:
    from bundle import build_bundle  # noqa: PLC0415

    entrypoint = (
        SCHEMAS_ROOT / "vc" / "source" / "envelope" / "credential-envelope.schema.json"
    )
    bundle = build_bundle(entrypoint)
    assert "x-bundle-generated-at" in bundle
    assert isinstance(bundle["x-bundle-generated-at"], str)
    assert bundle["x-bundle-generated-at"]


def test_build_bundle_raises_for_missing_ref_target(tmp_path: Path) -> None:
    """If a $ref points to a missing file, FileNotFoundError is raised."""
    from bundle import build_bundle  # noqa: PLC0415

    # Create a valid-looking schema inside SCHEMAS_ROOT to avoid containment rejection.
    schema_dir = SCHEMAS_ROOT / "_test_tmp"
    schema_dir.mkdir(exist_ok=True)
    schema_file = schema_dir / "bad_test.schema.json"
    schema_file.write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{INTERNAL_BASE}_test_tmp/bad_test.schema.json",
        "title": "Bad",
        "description": "Bad schema for test",
        "type": "object",
        "$ref": "./does-not-exist.schema.json",
    }))
    try:
        with pytest.raises(FileNotFoundError):
            build_bundle(schema_file)
    finally:
        schema_file.unlink(missing_ok=True)
        schema_dir.rmdir()


def test_bundle_ref_escape_raises_value_error(tmp_path: Path) -> None:
    """A $ref that resolves outside SCHEMAS_ROOT must raise ValueError."""
    from bundle import build_bundle  # noqa: PLC0415

    schema_dir = SCHEMAS_ROOT / "_test_tmp2"
    schema_dir.mkdir(exist_ok=True)
    schema_file = schema_dir / "escape_test.schema.json"
    schema_file.write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{INTERNAL_BASE}_test_tmp2/escape_test.schema.json",
        "title": "Escape",
        "description": "Escape test",
        "type": "object",
        "$ref": "../../outside.schema.json",
    }))
    try:
        with pytest.raises(ValueError, match="resolves outside SCHEMAS_ROOT"):
            build_bundle(schema_file)
    finally:
        schema_file.unlink(missing_ok=True)
        schema_dir.rmdir()
