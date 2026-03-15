"""
tests/unit/core/domains/test_domain_invariants.py
Verifies structural invariants of the core/ directory.

Tests:
  1. core/ directory exists
  2. No adapter imports in core/src/ Python files
  3. No ORM imports in core/src/ Python files
  4. No HTTP client imports in core/src/ Python files

These tests use static analysis (file scanning) — no service dependencies.
Marker: unit
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
CORE_ROOT = REPO_ROOT / "core"
CORE_SRC = CORE_ROOT / "src"


def _python_files_in(directory: Path) -> list[Path]:
    """Return all .py files under directory, or empty list if directory absent."""
    if not directory.exists():
        return []
    return list(directory.rglob("*.py"))


# ---------------------------------------------------------------------------
# Test 1: core directory exists
# ---------------------------------------------------------------------------


def test_repo_structure_core_package() -> None:
    """The core/ directory must exist at the repository root."""
    assert CORE_ROOT.exists(), (
        f"core/ directory not found at {CORE_ROOT}. "
        "core/ is the semantic kernel and must be present."
    )
    assert CORE_ROOT.is_dir(), f"{CORE_ROOT} exists but is not a directory"


# ---------------------------------------------------------------------------
# Test 2: No adapter imports in core
# ---------------------------------------------------------------------------


def test_core_has_no_adapter_imports() -> None:
    """
    core/src/ Python files must not import from adapters/, apps/, temporalio, or sqlalchemy.

    These imports represent boundary violations: core must not depend on integration
    layers, runtime surfaces, or workflow engines.
    """
    python_files = _python_files_in(CORE_SRC)
    if not python_files:
        pytest.skip("core/src/ not yet scaffolded — no Python files to scan")

    forbidden_patterns = [
        "from adapters",
        "import adapters",
        "from apps",
        "import apps",
        "import temporalio",
        "from temporalio",
        "import sqlalchemy",
        "from sqlalchemy",
    ]

    violations: list[str] = []
    for py_file in python_files:
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for pattern in forbidden_patterns:
            for lineno, line in enumerate(source.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if pattern in line:
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}:{lineno}: {line.strip()!r}")

    assert not violations, (
        f"Forbidden imports found in core/src/ ({len(violations)} violation(s)):\n"
        + "\n".join(f"  {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Test 3: No ORM imports in core
# ---------------------------------------------------------------------------


def test_core_has_no_orm_imports() -> None:
    """
    core/src/ Python files must not import ORM frameworks.

    ORM belongs in adapters (persistence layer), not in the semantic kernel.
    """
    python_files = _python_files_in(CORE_SRC)
    if not python_files:
        pytest.skip("core/src/ not yet scaffolded — no Python files to scan")

    forbidden_patterns = [
        "import sqlalchemy",
        "from sqlalchemy",
        "import django.db",
        "from django.db",
        "import peewee",
        "from peewee",
        "import tortoise",
        "from tortoise",
    ]

    violations: list[str] = []
    for py_file in python_files:
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for pattern in forbidden_patterns:
            for lineno, line in enumerate(source.splitlines(), 1):
                if line.strip().startswith("#"):
                    continue
                if pattern in line:
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}:{lineno}: {line.strip()!r}")

    assert not violations, (
        f"ORM imports found in core/src/ ({len(violations)} violation(s)):\n"
        + "\n".join(f"  {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Test 4: No HTTP client imports in core
# ---------------------------------------------------------------------------


def test_core_has_no_http_client_imports() -> None:
    """
    core/src/ Python files must not import HTTP client libraries.

    Network I/O belongs in adapters, not in the domain semantic kernel.
    """
    python_files = _python_files_in(CORE_SRC)
    if not python_files:
        pytest.skip("core/src/ not yet scaffolded — no Python files to scan")

    forbidden_patterns = [
        "import httpx",
        "from httpx",
        "import requests",
        "from requests",
        "import aiohttp",
        "from aiohttp",
        "import urllib.request",
    ]

    violations: list[str] = []
    for py_file in python_files:
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for pattern in forbidden_patterns:
            for lineno, line in enumerate(source.splitlines(), 1):
                if line.strip().startswith("#"):
                    continue
                if pattern in line:
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}:{lineno}: {line.strip()!r}")

    assert not violations, (
        f"HTTP client imports found in core/src/ ({len(violations)} violation(s)):\n"
        + "\n".join(f"  {v}" for v in violations)
    )
