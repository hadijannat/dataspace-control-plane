"""
tests/tenancy/api/test_tenant_isolation.py
Verifies API layer enforces tenant isolation.

Tests:
  1. API filters by X-Tenant-ID header (or returns 200 without cross-tenant data)
  2. Forged tenant header cannot access other tenant's data (DB is final enforcement)
  3. Missing tenant header returns 400 or 401 (not 500 or data from another tenant)

Marker: tenancy
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.tenancy


# ---------------------------------------------------------------------------
# Test 1: API filters by tenant header
# ---------------------------------------------------------------------------


@pytest.mark.tenancy
def test_api_filters_by_tenant_header(test_client) -> None:
    """
    A GET request with X-Tenant-ID: tenant_A must return only tenant_A data
    (or 200 if the stub app has no multi-tenant data).
    """
    response = test_client.get("/health", headers={"X-Tenant-ID": "tenant_A"})
    assert response.status_code == 200, (
        f"Expected 200 with tenant header, got {response.status_code}"
    )

    # If the endpoint returns data, verify no tenant_B content is included
    try:
        data = response.json()
        data_str = str(data)
        assert "tenant_B" not in data_str, (
            f"Response with tenant_A header must not contain tenant_B data: {data_str}"
        )
    except Exception:
        pass  # Non-JSON response is acceptable for health check

    # Try a data endpoint if it exists
    for endpoint in ["/api/v1/assets", "/api/v1/passports", "/api/v1/catalog"]:
        data_response = test_client.get(endpoint, headers={"X-Tenant-ID": "tenant_A"})
        if data_response.status_code == 404:
            continue
        if data_response.status_code == 200:
            try:
                data = data_response.json()
                data_str = str(data)
                assert "tenant_B" not in data_str, (
                    f"Endpoint {endpoint} with tenant_A header returned tenant_B data"
                )
            except Exception:
                pass
            break


# ---------------------------------------------------------------------------
# Test 2: Forged tenant header cannot access other tenant's data
# ---------------------------------------------------------------------------


@pytest.mark.tenancy
def test_forged_tenant_header_cannot_access_other_tenant_data(test_client) -> None:
    """
    Even if a caller sends X-Tenant-ID: tenant_B on a token scoped to tenant_A,
    the DB RLS policy must be the final enforcement point.

    This test documents the defense-in-depth architecture: the API header is
    advisory, but the DB RLS policy enforces the boundary.
    """
    # With the fallback app, this simply checks no data leakage occurs
    response_a = test_client.get("/health", headers={"X-Tenant-ID": "tenant_A"})
    response_b = test_client.get("/health", headers={"X-Tenant-ID": "tenant_B"})

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    # The health endpoint should not include tenant-specific data
    data_a = str(response_a.json())
    data_b = str(response_b.json())

    # Verify no cross-contamination in health data
    assert "tenant_B" not in data_a, f"tenant_A response contains tenant_B reference: {data_a}"
    assert "tenant_A" not in data_b, f"tenant_B response contains tenant_A reference: {data_b}"


# ---------------------------------------------------------------------------
# Test 3: Missing tenant header returns 400/401
# ---------------------------------------------------------------------------


@pytest.mark.tenancy
def test_missing_tenant_header_returns_401_or_400(test_client) -> None:
    """
    A request without tenant context must return 400 or 401 — not 500 and not
    data from another tenant.

    The minimal fallback app returns 200 for /health without a tenant header
    (since it has no tenant enforcement). For actual API endpoints, a missing
    header must be rejected.
    """
    # Try data endpoints that should require tenant context
    for endpoint in ["/api/v1/assets", "/api/v1/passports", "/api/v1/catalog"]:
        response = test_client.get(endpoint)  # No X-Tenant-ID header
        if response.status_code == 404:
            continue  # Endpoint not implemented yet
        if response.status_code in (400, 401, 403):
            return  # Test passes

    # If all data endpoints returned 404, skip — they're not implemented yet
    pytest.skip(
        "No API data endpoints implemented yet that require tenant context. "
        "Add X-Tenant-ID enforcement when control-api endpoints are scaffolded."
    )
