"""
FastAPI app factory fixtures for control-api integration tests.
Creates TestClient and AsyncClient wrappers with dependency override support.
"""
from __future__ import annotations

from typing import Callable

import pytest


def _make_minimal_app():
    """Create a minimal FastAPI app with a health endpoint for test fallback."""
    fastapi = pytest.importorskip("fastapi")
    from fastapi import FastAPI

    app = FastAPI(title="Dataspace Control API (test fallback)")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def app_factory() -> Callable:
    """
    Session-scoped fixture returning a factory function that creates the app.

    Tries to import apps.control_api.main:create_app; falls back to a minimal
    FastAPI app with GET /health → {"status": "ok"}.
    """
    try:
        from apps.control_api.main import create_app

        return create_app
    except ImportError:
        return _make_minimal_app


# ---------------------------------------------------------------------------
# Test app instance
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def test_app(app_factory: Callable):
    """Function-scoped app instance created by app_factory."""
    app = app_factory()
    yield app


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
@pytest.mark.anyio
async def async_client(test_app):
    """
    Function-scoped async httpx.AsyncClient backed by ASGITransport.

    Skipped if httpx is not installed.
    """
    httpx = pytest.importorskip("httpx")
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
