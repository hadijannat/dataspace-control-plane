"""
schemas/odrl/tests — Validates ODRL schema family.

Run:
    pytest schemas/odrl/tests/ -v
    pytest tests/unit -k odrl_schemas
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent.parent
ODRL_SOURCE = SCHEMAS_ROOT / "odrl" / "source"


def _example_dir(validity: str, artifact_id: str) -> Path:
    return SCHEMAS_ROOT / "odrl" / "examples" / validity / artifact_id

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
    return sorted(ODRL_SOURCE.rglob("*.schema.json"))


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_has_required_fields(schema_path: Path) -> None:
    schema = _load(schema_path)
    for field in ("$schema", "$id", "title", "description"):
        assert field in schema, f"{schema_path.name} missing '{field}'"


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_declares_2020_12(schema_path: Path) -> None:
    schema = _load(schema_path)
    assert "2020-12" in schema.get("$schema", ""), \
        f"{schema_path.name}: must use JSON Schema 2020-12"


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_validates_against_meta(schema_path: Path) -> None:
    schema = _load(schema_path)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)


def test_valid_offer_example(schema_registry) -> None:
    schema = _load(ODRL_SOURCE / "base" / "policy-offer.schema.json")
    example = _load(_example_dir("valid", "odrl.policy-offer") / "policy-offer-example.json")
    validator = jsonschema.Draft202012Validator(schema, registry=schema_registry)
    errors = list(validator.iter_errors(example))
    assert not errors, f"Valid example failed: {[e.message for e in errors]}"


def test_invalid_offer_missing_action(schema_registry) -> None:
    schema = _load(ODRL_SOURCE / "base" / "permission.schema.json")
    example = _load(_example_dir("invalid", "odrl.permission") / "missing-action.json")
    # The invalid example has a permission object without 'action'
    perm = example.get("permission", [{}])[0]
    validator = jsonschema.Draft202012Validator(schema, registry=schema_registry)
    errors = list(validator.iter_errors(perm))
    assert errors, "Invalid permission (missing action) should have failed"


def test_ast_schema_is_strict() -> None:
    """Canonical AST has additionalProperties: false — validate that."""
    schema = _load(ODRL_SOURCE / "ast" / "canonical-policy-ast.schema.json")
    assert schema.get("additionalProperties") is False


def test_manifest_exists() -> None:
    assert (SCHEMAS_ROOT / "odrl" / "manifest.yaml").exists()


def test_base_examples_do_not_use_profile_specific_terms() -> None:
    example = _load(_example_dir("valid", "odrl.policy-offer") / "policy-offer-example.json")
    text = json.dumps(example)
    assert "cx-policy:" not in text
