"""
schemas/aas/tests — Validates AAS schema family.

Run:
    pytest schemas/aas/tests/ -v
    pytest tests/unit -k aas_schemas
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent.parent
AAS_SOURCE = SCHEMAS_ROOT / "aas" / "source"
AAS_EXAMPLES_VALID = SCHEMAS_ROOT / "aas" / "examples" / "valid"
AAS_EXAMPLES_INVALID = SCHEMAS_ROOT / "aas" / "examples" / "invalid"

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
    return sorted(AAS_SOURCE.rglob("*.schema.json"))


def _build_registry(extra_families: list[str] | None = None) -> "referencing.Registry":
    """Build a local registry pre-loaded with all local schema files."""
    resources = []
    families = ["aas"] + (extra_families or [])
    for family in families:
        family_dir = SCHEMAS_ROOT / family
        if not family_dir.exists():
            continue
        for sf in family_dir.rglob("*.schema.json"):
            schema = json.loads(sf.read_text())
            if "$id" in schema:
                resources.append(
                    referencing.Resource.from_contents(schema)
                )
    registry = referencing.Registry().with_resources(
        [(r.id(), r) for r in resources]
    )
    return registry


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_has_required_fields(schema_path: Path) -> None:
    schema = _load(schema_path)
    for field in ("$schema", "$id", "title", "description"):
        assert field in schema, f"{schema_path.name} missing '{field}'"


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_declares_2020_12(schema_path: Path) -> None:
    schema = _load(schema_path)
    assert "2020-12" in schema.get("$schema", ""), \
        f"{schema_path.name}: must declare JSON Schema 2020-12"


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.stem)
def test_schema_validates_against_meta(schema_path: Path) -> None:
    schema = _load(schema_path)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)


def test_valid_shell_example() -> None:
    schema = _load(AAS_SOURCE / "profiles" / "shell.schema.json")
    example = _load(AAS_EXAMPLES_VALID / "shell-example.json")
    registry = _build_registry()
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    errors = list(validator.iter_errors(example))
    assert not errors, f"Valid example failed: {[e.message for e in errors]}"


def test_invalid_shell_missing_id() -> None:
    schema = _load(AAS_SOURCE / "profiles" / "shell.schema.json")
    example = _load(AAS_EXAMPLES_INVALID / "missing-id.json")
    registry = _build_registry()
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    errors = list(validator.iter_errors(example))
    assert errors, "Invalid example (missing id) should fail"


def test_security_schemas_are_separate_from_profiles() -> None:
    """Verify that security schemas are NOT in source/profiles/."""
    profile_files = {p.name for p in (AAS_SOURCE / "profiles").glob("*.schema.json")}
    security_names = {"access-rule", "subject-attributes", "object-attributes", "access-token-claims"}
    mixed = {f.removesuffix(".schema.json") for f in profile_files} & security_names
    assert not mixed, f"Security schemas should be in source/security/, not profiles/: {mixed}"


def test_manifest_exists() -> None:
    assert (SCHEMAS_ROOT / "aas" / "manifest.yaml").exists()


def test_no_pack_specific_terms_in_source() -> None:
    """Ensure no Catena-X or ESPR-specific terms are hardcoded in aas/ source schemas."""
    forbidden_terms = ["cx-policy:", "cx:Traceability", "espr:", "battery_passport"]
    violations = []
    for schema_path in _schema_files():
        content = schema_path.read_text()
        for term in forbidden_terms:
            if term in content:
                violations.append(f"{schema_path.name}: contains '{term}'")
    assert not violations, "Pack-specific terms found in aas/ source schemas:\n" + "\n".join(violations)
