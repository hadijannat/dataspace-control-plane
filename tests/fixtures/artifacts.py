"""
Artifact path fixtures for test evidence collection.
Playwright traces, Temporal histories, TCK XML, coverage XML.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def artifacts_base_dir() -> Path:
    """Session-scoped base directory for all test artifacts."""
    root = Path(os.environ.get("TEST_ARTIFACTS_DIR", Path(__file__).resolve().parent.parent / "_artifacts"))
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture(scope="session")
def playwright_artifacts_dir(artifacts_base_dir: Path) -> Path:
    """Session-scoped directory for Playwright traces and screenshots."""
    d = Path(__file__).resolve().parent.parent / "e2e" / "artifacts"
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
    d = Path(__file__).resolve().parent.parent / "compatibility"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture(scope="session")
def coverage_dir(artifacts_base_dir: Path) -> Path:
    """Session-scoped directory for coverage XML artifacts."""
    return Path(__file__).resolve().parent.parent.parent
