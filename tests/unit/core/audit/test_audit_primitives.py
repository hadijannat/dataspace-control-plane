"""
tests/unit/core/audit/test_audit_primitives.py
Unit tests for core audit primitive contracts.

Tests:
  1. core/ directory contains subdirectories (is not empty)
  2. No audit primitives in adapters/ that import directly from core audit
  3. Evidence-envelope schema exists at expected path

These are structural invariant checks — no service dependencies.
Marker: unit
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
CORE_ROOT = REPO_ROOT / "core"
ADAPTERS_SRC = REPO_ROOT / "adapters" / "src"
EVIDENCE_ENVELOPE_SCHEMA = (
    REPO_ROOT / "schemas" / "dpp" / "source" / "exports" / "evidence-envelope.schema.json"
)


# ---------------------------------------------------------------------------
# Test 1: core directory contains subdirectories
# ---------------------------------------------------------------------------


def test_core_audit_directory_exists() -> None:
    """core/ must exist and contain at least one subdirectory."""
    assert CORE_ROOT.exists(), f"core/ directory not found: {CORE_ROOT}"
    subdirs = [p for p in CORE_ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")]
    assert subdirs, f"core/ directory is empty — expected subdirectories: {CORE_ROOT}"


# ---------------------------------------------------------------------------
# Test 2: No audit primitives in adapters/ that import core audit
# ---------------------------------------------------------------------------


def test_no_audit_primitives_in_adapters() -> None:
    """
    adapters/src/ must not contain modules that directly import from core.audit.

    The adapter layer normalizes external protocols to core ports — it must not
    reach into core audit internals directly. Audit evidence is emitted by
    procedures/, not adapters/.
    """
    if not ADAPTERS_SRC.exists():
        pytest.skip("adapters/src/ not yet scaffolded — skipping adapter audit check")

    forbidden_import_patterns = [
        "from core.audit",
        "from core import audit",
        "import core.audit",
    ]

    violations: list[str] = []
    for py_file in ADAPTERS_SRC.rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for pattern in forbidden_import_patterns:
            for lineno, line in enumerate(source.splitlines(), 1):
                if line.strip().startswith("#"):
                    continue
                if pattern in line:
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)}:{lineno}: {line.strip()!r}"
                    )

    assert not violations, (
        f"Adapters must not import from core.audit directly ({len(violations)} violation(s)):\n"
        + "\n".join(f"  {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Test 3: Evidence envelope schema exists
# ---------------------------------------------------------------------------


def test_evidence_envelope_schema_exists() -> None:
    """
    schemas/dpp/source/exports/evidence-envelope.schema.json must exist.

    This schema defines the structure that procedure evidence envelopes must
    conform to. Without it, no evidence emission contract exists.
    """
    assert EVIDENCE_ENVELOPE_SCHEMA.exists(), (
        f"Evidence envelope schema not found: {EVIDENCE_ENVELOPE_SCHEMA}\n"
        "This schema is required for the procedures/ → tests/ evidence emission contract."
    )
    # Also verify it's valid JSON
    import json

    try:
        schema = json.loads(EVIDENCE_ENVELOPE_SCHEMA.read_text())
    except json.JSONDecodeError as exc:
        pytest.fail(f"Evidence envelope schema is not valid JSON: {exc}")

    assert "$id" in schema, "Evidence envelope schema must have a $id"
    assert "title" in schema, "Evidence envelope schema must have a title"
