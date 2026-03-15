"""
tests/compatibility/test_schema_meta_compliance.py
JSON Schema 2020-12 meta-compliance gate for all source schemas.

Verifies that every repo-authored schema:
  1. Declares the JSON Schema 2020-12 dialect in `$schema`.
  2. Has the four required metadata fields: $schema, $id, title, description.
  3. Uses an internal base URI for $id (offline-resolvable).
  4. Validates cleanly against the 2020-12 meta-schema (no structural errors).

Run:
    pytest tests/compatibility/test_schema_meta_compliance.py -v
    pytest tests/compatibility -k schema
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"
SCHEMA_FAMILIES = ["vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping", "_shared"]
INTERNAL_BASE = "https://dataspace-control-plane.internal/schemas/"
REQUIRED_FIELDS = ("$schema", "$id", "title", "description")

try:
    import jsonschema
    import jsonschema.validators
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

pytestmark = pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")


def _all_source_schemas() -> list[Path]:
    """Collect all *.schema.json files from source/ subdirectories across families."""
    schemas: list[Path] = []
    for family in SCHEMA_FAMILIES:
        family_dir = SCHEMAS_ROOT / family
        if not family_dir.exists():
            continue
        # Include both source/ subdirs and _shared/meta/ schemas
        schemas.extend(sorted(family_dir.rglob("*.schema.json")))
    return schemas


@pytest.mark.parametrize("schema_path", _all_source_schemas(), ids=lambda p: str(p.relative_to(SCHEMAS_ROOT)))
def test_declares_json_schema_2020_12(schema_path: Path) -> None:
    """Every source schema must declare JSON Schema draft 2020-12."""
    schema = json.loads(schema_path.read_text())
    dialect = schema.get("$schema", "")
    assert "2020-12" in dialect, (
        f"{schema_path.relative_to(SCHEMAS_ROOT)}: $schema must contain '2020-12', got '{dialect}'"
    )


@pytest.mark.parametrize("schema_path", _all_source_schemas(), ids=lambda p: str(p.relative_to(SCHEMAS_ROOT)))
def test_has_required_metadata_fields(schema_path: Path) -> None:
    """Every source schema must have $schema, $id, title, description."""
    schema = json.loads(schema_path.read_text())
    missing = [f for f in REQUIRED_FIELDS if f not in schema]
    assert not missing, (
        f"{schema_path.relative_to(SCHEMAS_ROOT)}: missing required fields: {missing}"
    )


@pytest.mark.parametrize("schema_path", _all_source_schemas(), ids=lambda p: str(p.relative_to(SCHEMAS_ROOT)))
def test_id_uses_internal_base_uri(schema_path: Path) -> None:
    """Every source schema $id must start with the internal base URI for offline resolution."""
    schema = json.loads(schema_path.read_text())
    schema_id = schema.get("$id", "")
    assert schema_id.startswith(INTERNAL_BASE), (
        f"{schema_path.relative_to(SCHEMAS_ROOT)}: $id must start with '{INTERNAL_BASE}', got '{schema_id}'"
    )


@pytest.mark.parametrize("schema_path", _all_source_schemas(), ids=lambda p: str(p.relative_to(SCHEMAS_ROOT)))
def test_validates_against_meta_schema(schema_path: Path) -> None:
    """Every source schema must be structurally valid per jsonschema meta-schema check."""
    schema = json.loads(schema_path.read_text())
    cls = jsonschema.validators.validator_for(schema)
    # check_schema raises SchemaError if the schema itself is structurally invalid
    cls.check_schema(schema)
