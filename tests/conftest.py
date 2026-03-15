"""
tests/conftest.py
Shared pytest configuration and session-scoped fixtures for the repo-wide test suite.

Provides:
  - CLI options: --live-services, --containers
  - Autouse marker enforcement (skip integration/chaos/tenancy/crypto without --live-services)
  - schema_registry: offline JSON Schema registry for $ref resolution
  - repo_root, schemas_root, data_dir, artifacts_dir path fixtures

Requirements: referencing (optional — schema_registry returns None if absent)
"""
from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path

import pytest

TESTS_ROOT = Path(__file__).resolve().parent

if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

pytest_plugins = [
    "fixtures.apps",
    "fixtures.artifacts",
    "fixtures.containers",
    "fixtures.kafka",
    "fixtures.keycloak",
    "fixtures.pack_profiles",
    "fixtures.postgres",
    "fixtures.temporal_env",
    "fixtures.toxiproxy",
    "fixtures.vault",
]
if importlib.util.find_spec("pytest_playwright") is not None:
    pytest_plugins.append("pytest_playwright.pytest_playwright")

REPO_ROOT = TESTS_ROOT.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"
SCHEMA_FAMILIES = ["_shared", "vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping"]

# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live-services",
        action="store_true",
        default=False,
        help="Enable integration, chaos, tenancy and crypto tests that require real containers.",
    )
    parser.addoption(
        "--containers",
        action="store_true",
        default=False,
        help="Start Testcontainers for suites that need them. Implies --live-services.",
    )


# ---------------------------------------------------------------------------
# Marker registration (keeps pytest --strict-markers happy)
# ---------------------------------------------------------------------------

_MARKERS = [
    ("unit", "pure logic only — no network, no containers, no wall-clock time"),
    ("integration", "real service or app boundary required"),
    ("e2e", "browser-driven end-to-end flow (Playwright)"),
    ("compatibility", "official TCK-driven protocol verification"),
    ("tenancy", "cross-tenant and legal-entity isolation boundary tests"),
    ("crypto", "cryptographic boundary and key-custody tests"),
    ("chaos", "failure-injection and recovery tests"),
    ("slow", ">30s — excluded from default local runs"),
    ("nightly", "nightly-only suites"),
]


def pytest_configure(config: pytest.Config) -> None:
    for name, description in _MARKERS:
        config.addinivalue_line("markers", f"{name}: {description}")


# ---------------------------------------------------------------------------
# Autouse enforcement fixture
# ---------------------------------------------------------------------------

_GUARDED_MARKS = {"integration", "chaos", "tenancy", "crypto", "e2e"}


@pytest.fixture(autouse=True)
def _enforce_marker_rules(request: pytest.FixtureRequest) -> None:
    """Skip live-service tests when --live-services is not passed."""
    config = request.config
    live = config.getoption("--live-services", default=False) or config.getoption(
        "--containers", default=False
    )
    if not live:
        item_marks = {m.name for m in request.node.iter_markers()}
        guarded = item_marks & _GUARDED_MARKS
        if guarded:
            pytest.skip(
                f"Pass --live-services to enable real-service tests (marks: {', '.join(sorted(guarded))})"
            )


# ---------------------------------------------------------------------------
# Schema registry builder
# ---------------------------------------------------------------------------


def _build_schema_registry():
    """Build a referencing.Registry pre-loaded with all local schema files by $id."""
    try:
        import referencing
    except ImportError:
        return None

    resources = []
    for family in SCHEMA_FAMILIES:
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


# ---------------------------------------------------------------------------
# Session fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def schema_registry():
    """Session-scoped local JSON Schema registry for offline $ref resolution."""
    return _build_schema_registry()


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def schemas_root(repo_root: Path) -> Path:
    """Absolute path to the schemas/ directory."""
    return repo_root / "schemas"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Absolute path to tests/data/ — golden fixtures and replay histories."""
    return Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="session")
def artifacts_dir() -> Path:
    """Absolute path to tests/e2e/artifacts/ — Playwright traces and test evidence."""
    return Path(__file__).resolve().parent / "e2e" / "artifacts"
