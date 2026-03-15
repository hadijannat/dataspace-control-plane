"""
schemas/enterprise-mapping/tests — Validates enterprise-mapping schema family.

Run:
    pytest schemas/enterprise-mapping/tests/ -v
    pytest tests/unit -k enterprise_mapping_schemas
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent.parent
EM_SOURCE = SCHEMAS_ROOT / "enterprise-mapping" / "source"
EM_EXAMPLES_VALID = SCHEMAS_ROOT / "enterprise-mapping" / "examples" / "valid"
EM_EXAMPLES_INVALID = SCHEMAS_ROOT / "enterprise-mapping" / "examples" / "invalid"

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
    return sorted(EM_SOURCE.rglob("*.schema.json"))


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


def test_valid_mapping_spec(schema_registry) -> None:
    schema = _load(EM_SOURCE / "mapping" / "mapping-spec.schema.json")
    example = _load(EM_EXAMPLES_VALID / "mapping-spec-example.json")
    validator = jsonschema.Draft202012Validator(schema, registry=schema_registry)
    errors = list(validator.iter_errors(example))
    assert not errors, f"Valid mapping spec failed: {[e.message for e in errors]}"


def test_invalid_mapping_spec_missing_lineage() -> None:
    schema = _load(EM_SOURCE / "mapping" / "field-mapping.schema.json")
    example = _load(EM_EXAMPLES_INVALID / "missing-lineage.json")
    # The invalid example has a fieldMapping entry without 'lineage'
    field_mapping = example.get("fieldMappings", [{}])[0]
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(field_mapping))
    assert errors, "Field mapping without lineage should fail"


def test_source_kind_refs_have_kind_discriminator() -> None:
    """All source-kind schemas must have a const 'kind' discriminator."""
    source_kinds = sorted((EM_SOURCE / "source-kinds").glob("*.schema.json"))
    for sp in source_kinds:
        schema = _load(sp)
        kind_prop = schema.get("properties", {}).get("kind", {})
        assert "const" in kind_prop, f"{sp.name}: 'kind' property must have a const discriminator"


def test_mapping_spec_requires_lineage_in_field_mapping() -> None:
    """mapping-spec requires fieldMappings; each must have 'lineage' per field-mapping schema."""
    schema = _load(EM_SOURCE / "mapping" / "field-mapping.schema.json")
    required = schema.get("required", [])
    assert "lineage" in required, "lineage must be required in field-mapping.schema.json"


def test_manifest_exists() -> None:
    assert (SCHEMAS_ROOT / "enterprise-mapping" / "manifest.yaml").exists()


def test_execution_schemas_are_separate_from_definition_schemas() -> None:
    """Execution schemas must be in source/execution/, not in source/mapping/."""
    exec_names = {"mapping-run", "mapping-result"}
    mapping_files = {p.stem for p in (EM_SOURCE / "mapping").glob("*.schema.json")}
    mixed = exec_names & mapping_files
    assert not mixed, f"Execution schemas in source/mapping/: {mixed}"
