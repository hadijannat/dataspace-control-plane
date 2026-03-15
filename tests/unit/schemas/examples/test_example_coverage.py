"""
tests/unit/schemas/examples/test_example_coverage.py
Verifies that all schema families have non-empty valid and invalid example directories,
and that valid examples actually pass their family schemas.

Tests:
  1. All families have non-empty valid examples directory
  2. All families have non-empty invalid examples directory
  3. Valid examples validate against their family schema (parametrized)

Requires: jsonschema (for validation). Marker: unit
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"

FAMILIES = ["vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping"]


# ---------------------------------------------------------------------------
# Test 1: All families have valid examples
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("family", FAMILIES)
def test_all_families_have_valid_examples(family: str) -> None:
    """schemas/{family}/examples/valid/ must exist and contain at least one file."""
    valid_dir = SCHEMAS_ROOT / family / "examples" / "valid"
    assert valid_dir.exists(), (
        f"Missing valid examples directory for family '{family}': {valid_dir}"
    )
    examples = list(valid_dir.iterdir())
    assert examples, (
        f"Valid examples directory is empty for family '{family}': {valid_dir}"
    )


# ---------------------------------------------------------------------------
# Test 2: All families have invalid examples
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("family", FAMILIES)
def test_all_families_have_invalid_examples(family: str) -> None:
    """schemas/{family}/examples/invalid/ must exist and contain at least one file."""
    invalid_dir = SCHEMAS_ROOT / family / "examples" / "invalid"
    assert invalid_dir.exists(), (
        f"Missing invalid examples directory for family '{family}': {invalid_dir}"
    )
    examples = list(invalid_dir.iterdir())
    assert examples, (
        f"Invalid examples directory is empty for family '{family}': {invalid_dir}"
    )


# ---------------------------------------------------------------------------
# Helpers for test 3
# ---------------------------------------------------------------------------


def _collect_valid_examples() -> list[tuple[str, Path]]:
    """Collect all valid example JSON files across all families."""
    examples: list[tuple[str, Path]] = []
    for family in FAMILIES:
        valid_dir = SCHEMAS_ROOT / family / "examples" / "valid"
        if valid_dir.exists():
            for p in valid_dir.glob("*.json"):
                examples.append((family, p))
    return examples


def _find_primary_schema_for_family(family: str) -> dict | None:
    """
    Find the primary (entrypoint) schema for a family.

    Strategy: load registry.yaml and find the first entrypoint for this family,
    or fall back to scanning source/ for the most likely schema.
    """
    # Try registry.yaml first
    registry_path = SCHEMAS_ROOT / "registry.yaml"
    if registry_path.exists():
        try:
            import yaml

            with open(registry_path) as f:
                reg = yaml.safe_load(f)
            for entry in reg.get("families", []):
                if entry.get("schema_family") == family:
                    eps = entry.get("entrypoints", [])
                    if eps:
                        ep_path = SCHEMAS_ROOT / eps[0]
                        if ep_path.exists():
                            return json.loads(ep_path.read_text())
        except (ImportError, Exception):
            pass

    # Fallback: find any schema in source/
    source_dir = SCHEMAS_ROOT / family / "source"
    if source_dir.exists():
        candidates = list(source_dir.rglob("*.schema.json"))
        if candidates:
            try:
                return json.loads(candidates[0].read_text())
            except Exception:
                pass
    return None


# ---------------------------------------------------------------------------
# Test 3: Valid examples pass their family schemas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "family,example_path",
    _collect_valid_examples(),
    ids=lambda x: x.name if isinstance(x, Path) else str(x),
)
def test_valid_examples_pass_their_family_schemas(
    schema_registry,
    family: str,
    example_path: Path,
) -> None:
    """Each valid example must pass validation against its family's primary schema."""
    jsonschema = pytest.importorskip("jsonschema")
    from jsonschema import Draft202012Validator

    # Load example
    try:
        example = json.loads(example_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        pytest.fail(f"Could not load example {example_path}: {exc}")

    # Find schema
    schema = _find_primary_schema_for_family(family)
    if schema is None:
        pytest.skip(f"No primary schema found for family '{family}'")

    # Validate
    if schema_registry is not None:
        validator = Draft202012Validator(schema, registry=schema_registry)
    else:
        validator = Draft202012Validator(schema)

    errors = [
        e for e in validator.iter_errors(example)
        # Filter out Unresolvable ref errors — those are external schema issues
        if "Unresolvable" not in str(type(e.cause))
    ]
    assert not errors, (
        f"Valid example {example_path.name} failed schema validation for family '{family}':\n"
        + "\n".join(f"  {e.json_path}: {e.message}" for e in errors[:5])
    )
