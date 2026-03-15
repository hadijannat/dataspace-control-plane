"""
Artifact path fixtures for test evidence collection.
Playwright traces, Temporal histories, TCK XML, coverage XML.
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def artifacts_base_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session-scoped base directory for all test artifacts."""
    return tmp_path_factory.mktemp("artifacts")


@pytest.fixture(scope="session")
def playwright_artifacts_dir(artifacts_base_dir: Path) -> Path:
    """Session-scoped directory for Playwright traces and screenshots."""
    d = artifacts_base_dir / "playwright"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture(scope="session")
def temporal_histories_dir() -> Path:
    """
    Session-scoped path to the golden Temporal workflow history directory.

    Created if absent so that the first run does not fail.
    """
    d = Path(__file__).resolve().parent.parent / "data" / "temporal_histories"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture(scope="session")
def tck_reports_dir(artifacts_base_dir: Path) -> Path:
    """Session-scoped directory for TCK JUnit XML reports."""
    d = artifacts_base_dir / "tck"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture(scope="session")
def coverage_dir(artifacts_base_dir: Path) -> Path:
    """Session-scoped directory for coverage XML artifacts."""
    d = artifacts_base_dir / "coverage"
    d.mkdir(parents=True, exist_ok=True)
    return d
