"""
schemas/conftest.py
Shared pytest fixtures for all schema family tests.
Provides a pre-loaded local jsonschema registry so $ref resolution works
without live network access.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMAS_ROOT = Path(__file__).resolve().parent
FAMILIES = ["_shared", "vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping"]


def _build_schema_registry():
    """Build a referencing.Registry pre-loaded with all local schema files."""
    try:
        import referencing
    except ImportError:
        return None

    resources = []
    for family in FAMILIES:
        family_dir = SCHEMAS_ROOT / family
        if not family_dir.exists():
            continue
        for sf in family_dir.rglob("*.schema.json"):
            try:
                schema = json.loads(sf.read_text())
                if "$id" in schema:
                    resources.append(referencing.Resource.from_contents(schema))
            except (json.JSONDecodeError, OSError):
                pass

    return referencing.Registry().with_resources(
        [(r.id(), r) for r in resources]
    )


@pytest.fixture(scope="session")
def schema_registry():
    """Session-scoped local JSON Schema registry for offline $ref resolution."""
    return _build_schema_registry()


def example_dir(family: str, validity: str, artifact_id: str) -> Path:
    return SCHEMAS_ROOT / family / "examples" / validity / artifact_id
