"""
tests/schemas/vc — Validates VC schema family.

Run:
    pytest schemas/vc/tests/ -v
    pytest tests/unit -k vc_schemas
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent.parent
VC_SOURCE = SCHEMAS_ROOT / "vc" / "source"
VC_EXAMPLES_VALID = SCHEMAS_ROOT / "vc" / "examples" / "valid"
VC_EXAMPLES_INVALID = SCHEMAS_ROOT / "vc" / "examples" / "invalid"

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
    return sorted(VC_SOURCE.rglob("*.schema.json"))


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_has_required_fields(schema_path: Path) -> None:
    schema = _load(schema_path)
    for field in ("$schema", "$id", "title", "description"):
        assert field in schema, f"{schema_path.name} missing required field '{field}'"


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_declares_2020_12(schema_path: Path) -> None:
    schema = _load(schema_path)
    assert "2020-12" in schema.get("$schema", ""), (
        f"{schema_path.name}: must use JSON Schema 2020-12 dialect"
    )


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_validates_against_meta(schema_path: Path) -> None:
    schema = _load(schema_path)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)


def test_valid_credential_example(schema_registry) -> None:
    schema = _load(VC_SOURCE / "envelope" / "credential-envelope.schema.json")
    example = _load(VC_EXAMPLES_VALID / "credential-example.json")
    validator = jsonschema.Draft202012Validator(schema, registry=schema_registry)
    errors = list(validator.iter_errors(example))
    assert not errors, f"Valid example failed validation: {[e.message for e in errors]}"


def test_invalid_credential_missing_issuer(schema_registry) -> None:
    schema = _load(VC_SOURCE / "envelope" / "credential-envelope.schema.json")
    example = _load(VC_EXAMPLES_INVALID / "missing-issuer.json")
    validator = jsonschema.Draft202012Validator(schema, registry=schema_registry)
    errors = list(validator.iter_errors(example))
    assert errors, "Invalid example should have failed validation but passed"


def test_manifest_exists() -> None:
    manifest = SCHEMAS_ROOT / "vc" / "manifest.yaml"
    assert manifest.exists(), "manifest.yaml must exist in schemas/vc/"


def test_all_source_schemas_have_internal_id() -> None:
    internal_base = "https://dataspace-control-plane.internal/schemas/"
    for schema_path in _schema_files():
        schema = _load(schema_path)
        schema_id = schema.get("$id", "")
        assert schema_id.startswith(internal_base), (
            f"{schema_path.name}: $id must start with '{internal_base}', got '{schema_id}'"
        )
