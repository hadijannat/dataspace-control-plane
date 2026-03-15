"""
schemas/dpp/tests — Validates DPP schema family.

Run:
    pytest schemas/dpp/tests/ -v
    pytest tests/unit -k dpp_schemas
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent.parent
DPP_SOURCE = SCHEMAS_ROOT / "dpp" / "source"
DPP_EXAMPLES_VALID = SCHEMAS_ROOT / "dpp" / "examples" / "valid"
DPP_EXAMPLES_INVALID = SCHEMAS_ROOT / "dpp" / "examples" / "invalid"

try:
    import jsonschema
    import jsonschema.validators
    import referencing
    import referencing.jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

pytestmark = pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _schema_files() -> list[Path]:
    return sorted(DPP_SOURCE.rglob("*.schema.json"))


def _build_registry() -> "referencing.Registry":
    resources = []
    for family in ["dpp", "aas"]:
        for sf in (SCHEMAS_ROOT / family).rglob("*.schema.json"):
            schema = json.loads(sf.read_text())
            if "$id" in schema:
                resources.append(referencing.Resource.from_contents(schema))
    return referencing.Registry().with_resources([(r.id(), r) for r in resources])


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


def test_valid_passport_example() -> None:
    schema = _load(DPP_SOURCE / "base" / "passport-envelope.schema.json")
    example = _load(DPP_EXAMPLES_VALID / "passport-example.json")
    registry = _build_registry()
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    errors = list(validator.iter_errors(example))
    assert not errors, f"Valid example failed: {[e.message for e in errors]}"


def test_invalid_passport_missing_subject() -> None:
    schema = _load(DPP_SOURCE / "base" / "passport-envelope.schema.json")
    example = _load(DPP_EXAMPLES_INVALID / "missing-subject.json")
    registry = _build_registry()
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    errors = list(validator.iter_errors(example))
    assert errors, "Invalid example (missing subject) should fail"


def test_base_has_no_regulation_specific_properties() -> None:
    """Verify that base/ schemas don't define ESPR/battery-specific property names."""
    # Only check schema properties keys, not descriptions or metadata references.
    forbidden_prop_names = [
        "battery_chemistry", "carbon_footprint_kg_co2eq", "annex_xiii_fields",
        "delegated_act_ref", "repurposing_obligation", "espr_product_category",
    ]
    base_schemas = sorted((DPP_SOURCE / "base").glob("*.schema.json"))
    violations = []
    for sp in base_schemas:
        schema = json.loads(sp.read_text())
        props = set(schema.get("properties", {}).keys())
        for term in forbidden_prop_names:
            if term in props:
                violations.append(f"{sp.name}: property '{term}' is regulation-specific")
    assert not violations, "Regulation-specific properties in base/ schemas:\n" + "\n".join(violations)


def test_lifecycle_states_include_terminal() -> None:
    schema = _load(DPP_SOURCE / "base" / "passport-lifecycle.schema.json")
    states = schema["properties"]["currentState"]["enum"]
    assert "recycled_ceased" in states, "recycled_ceased must be a terminal state"
    assert "active" in states


def test_link_types_include_repurposed_and_remanufactured() -> None:
    schema = _load(DPP_SOURCE / "base" / "passport-link.schema.json")
    link_types = schema["properties"]["linkType"]["enum"]
    assert "repurposed" in link_types
    assert "remanufactured" in link_types


def test_manifest_exists() -> None:
    assert (SCHEMAS_ROOT / "dpp" / "manifest.yaml").exists()
