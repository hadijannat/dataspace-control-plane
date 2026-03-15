"""
schemas/metering/tests — Validates metering schema family.

Run:
    pytest schemas/metering/tests/ -v
    pytest tests/unit -k metering_schemas
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent.parent
METERING_SOURCE = SCHEMAS_ROOT / "metering" / "source"
METERING_EXAMPLES_VALID = SCHEMAS_ROOT / "metering" / "examples" / "valid"
METERING_EXAMPLES_INVALID = SCHEMAS_ROOT / "metering" / "examples" / "invalid"

try:
    import jsonschema
    import jsonschema.validators
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

pytestmark = pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _schema_files() -> list[Path]:
    return sorted(METERING_SOURCE.rglob("*.schema.json"))


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_has_required_fields(schema_path: Path) -> None:
    schema = _load(schema_path)
    for field in ("$schema", "$id", "title", "description"):
        assert field in schema, f"{schema_path.name} missing '{field}'"


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_uses_2020_12(schema_path: Path) -> None:
    schema = _load(schema_path)
    assert "2020-12" in schema.get("$schema", "")


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_validates_against_meta(schema_path: Path) -> None:
    schema = _load(schema_path)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)


def test_valid_usage_record(schema_registry) -> None:
    schema = _load(METERING_SOURCE / "business" / "usage-record.schema.json")
    example = _load(METERING_EXAMPLES_VALID / "usage-record-example.json")
    validator = jsonschema.Draft202012Validator(schema, registry=schema_registry)
    errors = list(validator.iter_errors(example))
    assert not errors, f"Valid example failed: {[e.message for e in errors]}"


def test_invalid_usage_record_missing_tenant(schema_registry) -> None:
    schema = _load(METERING_SOURCE / "business" / "usage-record.schema.json")
    example = _load(METERING_EXAMPLES_INVALID / "missing-tenant.json")
    validator = jsonschema.Draft202012Validator(schema, registry=schema_registry)
    errors = list(validator.iter_errors(example))
    assert errors, "Missing tenantId should fail validation"


def test_usage_record_has_no_transport_dependency() -> None:
    """usage-record.schema.json must not directly reference CloudEvents."""
    schema = _load(METERING_SOURCE / "business" / "usage-record.schema.json")
    content = json.dumps(schema)
    assert "cloudevents" not in content.lower()
    assert "specversion" not in content


def test_transport_uses_cloudevents_specversion() -> None:
    schema = _load(METERING_SOURCE / "transport" / "cloudevents-envelope.schema.json")
    specver = schema["properties"]["specversion"]["const"]
    assert specver == "1.0"


def test_manifest_exists() -> None:
    assert (SCHEMAS_ROOT / "metering" / "manifest.yaml").exists()
