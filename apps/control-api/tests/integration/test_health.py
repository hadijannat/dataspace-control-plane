"""Basic liveness/readiness smoke test using FastAPI TestClient with lifespan."""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_liveness():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_is_import_safe_without_external_services():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code in {200, 503}
    assert response.json()["status"] in {"ok", "degraded"}


@pytest.mark.asyncio
async def test_docs_are_gated_without_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/docs")
    assert response.status_code in {401, 403}
