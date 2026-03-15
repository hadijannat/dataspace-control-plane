"""
tests/unit/schemas/bundling/test_bundle.py
Unit tests for the schemas/tools/bundle.py bundler.

Tests:
  1. Single schema with no $refs — bundle output identical to input
  2. Local $ref causes $defs section in bundle
  3. External http $refs are left intact (not inlined)
  4. Schema without $id — bundle does not raise

Requires: schemas/tools/bundle.py (imports via sys.path manipulation)
Marker: unit
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
TOOLS_DIR = REPO_ROOT / "schemas" / "tools"

# Add tools directory to sys.path so we can import bundle.py
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

try:
    import bundle as _bundle_module  # type: ignore

    _BUNDLE_AVAILABLE = True
except ImportError:
    _BUNDLE_AVAILABLE = False


def _require_bundle():
    if not _BUNDLE_AVAILABLE:
        pytest.skip("schemas/tools/bundle.py not importable")


# ---------------------------------------------------------------------------
# Test 1: Single schema with no $refs — output identical to input
# ---------------------------------------------------------------------------


def test_bundle_single_schema_no_refs() -> None:
    """Bundling a schema with no $refs must return the same schema structure."""
    _require_bundle()

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://dataspace-control-plane.internal/schemas/test/no-refs.schema.json",
        "title": "No Refs Schema",
        "description": "A schema with no $ref entries",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
        },
    }

    with tempfile.NamedTemporaryFile(suffix=".schema.json", mode="w", delete=False) as tmp:
        json.dump(schema, tmp)
        tmp_path = Path(tmp.name)

    try:
        result = _bundle_module.bundle(tmp_path)
        assert result["title"] == schema["title"]
        assert result["type"] == schema["type"]
        assert result["properties"]["name"]["type"] == "string"
        # $defs may be added but must be empty or not present
        assert not result.get("$defs") or all(
            not v for v in result["$defs"].values()
        ), f"Unexpected $defs content for no-ref schema: {result.get('$defs')}"
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test 2: Local $ref causes $defs section
# ---------------------------------------------------------------------------


def test_bundle_adds_defs_for_local_refs() -> None:
    """A schema with a local $ref must produce a bundle with $defs containing the referenced schema."""
    _require_bundle()

    internal_base = "https://dataspace-control-plane.internal/schemas/"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        schemas_subdir = tmp_root / "test"
        schemas_subdir.mkdir()

        # Referenced schema
        ref_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{internal_base}test/referenced.schema.json",
            "title": "Referenced",
            "type": "object",
            "properties": {"value": {"type": "integer"}},
        }
        ref_path = schemas_subdir / "referenced.schema.json"
        ref_path.write_text(json.dumps(ref_schema))

        # Root schema referencing the above
        root_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{internal_base}test/root.schema.json",
            "title": "Root",
            "type": "object",
            "properties": {
                "item": {"$ref": f"{internal_base}test/referenced.schema.json"},
            },
        }
        root_path = schemas_subdir / "root.schema.json"
        root_path.write_text(json.dumps(root_schema))

        # Monkey-patch SCHEMAS_ROOT temporarily
        original_root = _bundle_module.SCHEMAS_ROOT
        _bundle_module.SCHEMAS_ROOT = tmp_root
        try:
            result = _bundle_module.bundle(root_path)
        finally:
            _bundle_module.SCHEMAS_ROOT = original_root

        assert "$defs" in result, "Bundle must have $defs when local $refs are present"
        assert result["$defs"], "Bundle $defs must be non-empty when local $refs are present"


# ---------------------------------------------------------------------------
# Test 3: External http $refs left intact
# ---------------------------------------------------------------------------


def test_bundle_leaves_external_http_refs_intact() -> None:
    """External http/https $refs must not be inlined — they must remain as $ref strings."""
    _require_bundle()

    external_ref = "https://json-schema.org/draft/2020-12/schema"

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://dataspace-control-plane.internal/schemas/test/external-ref.schema.json",
        "title": "External Ref Schema",
        "properties": {
            "meta": {"$ref": external_ref},
        },
    }

    with tempfile.NamedTemporaryFile(suffix=".schema.json", mode="w", delete=False) as tmp:
        json.dump(schema, tmp)
        tmp_path = Path(tmp.name)

    try:
        result = _bundle_module.bundle(tmp_path)
        result_str = json.dumps(result)
        assert external_ref in result_str, (
            f"External $ref {external_ref!r} must be preserved in bundle output"
        )
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test 4: Schema without $id does not raise
# ---------------------------------------------------------------------------


def test_bundle_handles_schema_without_id() -> None:
    """Bundling a schema without $id must not raise — $id is optional per JSON Schema spec."""
    _require_bundle()

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "No ID Schema",
        "type": "string",
    }

    with tempfile.NamedTemporaryFile(suffix=".schema.json", mode="w", delete=False) as tmp:
        json.dump(schema, tmp)
        tmp_path = Path(tmp.name)

    try:
        # Must not raise
        result = _bundle_module.bundle(tmp_path)
        assert result is not None
        assert result["type"] == "string"
    finally:
        tmp_path.unlink(missing_ok=True)
