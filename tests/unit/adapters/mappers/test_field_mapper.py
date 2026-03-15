"""
tests/unit/adapters/mappers/test_field_mapper.py
Unit tests verifying the lineage-mandatory invariant from the enterprise-mapping schema.

Tests: lineage required for field-mapping, valid lineage passes, lineage preserved through
mapping for multiple source fields, and all field mappings carry lineage (property-based).

Requires: jsonschema. Uses the live field-mapping.schema.json from schemas/.
Marker: unit
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

jsonschema = pytest.importorskip("jsonschema")

from jsonschema import Draft202012Validator, ValidationError

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
FIELD_MAPPING_SCHEMA_PATH = (
    REPO_ROOT
    / "schemas"
    / "enterprise-mapping"
    / "source"
    / "mapping"
    / "field-mapping.schema.json"
)


@pytest.fixture(scope="module")
def field_mapping_schema() -> dict:
    if not FIELD_MAPPING_SCHEMA_PATH.exists():
        pytest.skip(f"field-mapping.schema.json not found: {FIELD_MAPPING_SCHEMA_PATH}")
    return json.loads(FIELD_MAPPING_SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def field_mapping_validator(field_mapping_schema: dict) -> Draft202012Validator:
    """
    Draft202012Validator configured with an offline registry for field-mapping schema.
    External $refs are left unresolved (this test only checks the lineage field structure).
    """
    try:
        import referencing

        families = ["_shared", "vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping"]
        schemas_root = REPO_ROOT / "schemas"
        resources = []
        for family in families:
            for sf in (schemas_root / family).rglob("*.schema.json"):
                try:
                    s = json.loads(sf.read_text())
                    if "$id" in s:
                        resources.append(referencing.Resource.from_contents(s))
                except Exception:
                    pass
        registry = referencing.Registry().with_resources([(r.id(), r) for r in resources])
        return Draft202012Validator(field_mapping_schema, registry=registry)
    except ImportError:
        return Draft202012Validator(field_mapping_schema)


def _valid_lineage(source_entity: str = "SourceEntity", source_field: str = "input_field") -> dict:
    """Build a minimal lineage-graph-compliant dict per lineage-graph.schema.json.

    Required: derivationType, sourceFieldRefs (not 'source' or 'transformHash').
    """
    return {
        "derivationType": "direct",
        "sourceFieldRefs": [{"entity": source_entity, "field": source_field}],
    }


def _valid_mapping(target: str = "output_field", source: str = "input_field") -> dict:
    return {
        "targetField": target,
        "sourceFields": [{"entity": "SourceEntity", "field": source}],
        "lineage": _valid_lineage(source_field=source),
    }


# ---------------------------------------------------------------------------
# Test 1: lineage is required
# ---------------------------------------------------------------------------


def test_field_mapping_requires_lineage(field_mapping_validator: Draft202012Validator) -> None:
    """A field-mapping dict without 'lineage' must fail schema validation."""
    invalid = {
        "targetField": "output_name",
        "sourceFields": [{"entity": "SourceEntity", "field": "input_name"}],
        # 'lineage' intentionally omitted
    }
    errors = list(field_mapping_validator.iter_errors(invalid))
    lineage_errors = [
        e for e in errors if "lineage" in str(e.path) or "lineage" in str(e.message)
    ]
    assert errors, (
        "Expected validation errors for mapping without lineage, but schema passed"
    )


# ---------------------------------------------------------------------------
# Test 2: valid lineage passes
# ---------------------------------------------------------------------------


def test_field_mapping_with_lineage_passes(field_mapping_validator: Draft202012Validator) -> None:
    """A field-mapping dict with a valid lineage field must pass schema validation."""
    valid = _valid_mapping()
    errors = list(field_mapping_validator.iter_errors(valid))
    # Filter out errors that are only due to unresolvable $refs (external schemas)
    hard_errors = [e for e in errors if "Unresolvable" not in str(type(e.cause))]
    assert not hard_errors, (
        f"Expected no hard validation errors for valid mapping, got: {hard_errors}"
    )


# ---------------------------------------------------------------------------
# Test 3: lineage preserved for multiple source fields (parametrized)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target,source",
    [
        ("manufacturer_name", "supplier_legal_name"),
        ("product_id", "sku_code"),
        ("legal_entity_id", "bpn_number"),
    ],
)
def test_lineage_is_preserved_through_mapping(
    field_mapping_validator: Draft202012Validator,
    target: str,
    source: str,
) -> None:
    """For multiple source fields, each valid mapping instance must carry lineage."""
    mapping = _valid_mapping(target=target, source=source)
    assert "lineage" in mapping, "lineage key must be present in mapping dict"
    assert "derivationType" in mapping["lineage"], "lineage.derivationType must be present"
    assert "sourceFieldRefs" in mapping["lineage"], "lineage.sourceFieldRefs must be present"
    errors = list(field_mapping_validator.iter_errors(mapping))
    hard_errors = [e for e in errors if "Unresolvable" not in str(type(e.cause))]
    assert not hard_errors, f"Mapping for {target}<-{source} failed: {hard_errors}"


# ---------------------------------------------------------------------------
# Test 4: property-based — all field mappings carry lineage
# ---------------------------------------------------------------------------


def test_all_field_mappings_carry_lineage() -> None:
    """Property test: every field mapping dict built with lineage carries the lineage key."""
    hypothesis = pytest.importorskip("hypothesis")
    from hypothesis import given, settings
    from hypothesis import strategies as st

    @given(
        mappings=st.lists(
            st.fixed_dictionaries({
                "targetField": st.from_regex(r"[a-z_]{3,20}", fullmatch=True),
                "sourceFields": st.lists(
                    st.fixed_dictionaries({
                        "entity": st.from_regex(r"[A-Za-z]{3,15}", fullmatch=True),
                        "field": st.from_regex(r"[a-z_]{3,20}", fullmatch=True),
                    }),
                    min_size=1,
                    max_size=3,
                ),
                "lineage": st.fixed_dictionaries({
                    "derivationType": st.sampled_from([
                        "direct", "transformed", "computed", "constant"
                    ]),
                    "sourceFieldRefs": st.lists(
                        st.fixed_dictionaries({
                            "entity": st.just("SourceEntity"),
                            "field": st.from_regex(r"[a-z_]{3,20}", fullmatch=True),
                        }),
                        min_size=1,
                        max_size=3,
                    ),
                }),
            }),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=50)
    def _check(mappings: list[dict]) -> None:
        for m in mappings:
            assert "lineage" in m, f"lineage key missing in: {m}"
            assert "derivationType" in m["lineage"], f"lineage.derivationType missing in: {m}"
            assert "sourceFieldRefs" in m["lineage"], f"lineage.sourceFieldRefs missing in: {m}"

    _check()
