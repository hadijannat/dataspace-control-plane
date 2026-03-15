"""
FastAPI app factory fixtures for control-api integration tests.
Creates TestClient and AsyncClient wrappers with dependency override support.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

import pytest


CONTROL_API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "control-api"


def _ensure_control_api_import_path() -> None:
    """Make the control-api package importable without relying on editable installs."""
    if str(CONTROL_API_ROOT) not in sys.path:
        sys.path.insert(0, str(CONTROL_API_ROOT))


def _configure_control_api_env() -> None:
    """Force the control-api app into test-safe debug mode before import."""
    os.environ.setdefault("CONTROL_API_DEBUG", "true")
    os.environ.setdefault(
        "CONTROL_API_STREAM_TICKET_SECRET",
        "dev-stream-ticket-secret-dev-stream-ticket-secret",
    )


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def app_factory() -> Callable:
    """
    Session-scoped fixture returning a factory function that creates the app.

    Imports the real control-api factory from apps/control-api/app/main.py.
    The repo-wide integration spine must never silently fall back to a fake app.
    """
    _configure_control_api_env()
    _ensure_control_api_import_path()
    try:
        from app.main import create_app
    except ImportError as exc:  # pragma: no cover - surfaced as fixture setup failure
        raise RuntimeError(
            "Could not import the real control-api app factory from apps/control-api/app/main.py"
        ) from exc
    return create_app


# ---------------------------------------------------------------------------
# Test app instance
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def test_app(app_factory: Callable):
    """Function-scoped app instance created by app_factory."""
    app = app_factory()
    yield app


@pytest.fixture(scope="function")
def app_dependency_overrides(test_app):
    """
    Function-scoped dependency override mapping for narrow integration-test substitutions.

    Tests may mutate the returned mapping; it is always cleared on teardown.
    """
    yield test_app.dependency_overrides
    test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Synchronous test client
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def test_client(test_app):
    """
    Function-scoped fastapi.testclient.TestClient.

    Uses context manager so lifespan events (startup/shutdown) run.
    Skipped if fastapi or httpx are not installed.
    """
    fastapi = pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    with TestClient(test_app) as client:
        yield client


# ---------------------------------------------------------------------------
# Async test client
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
async def async_client(test_app):
    """
    Function-scoped async httpx.AsyncClient backed by ASGITransport.

    Skipped if httpx is not installed.
    """
    httpx = pytest.importorskip("httpx")
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
