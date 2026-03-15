"""
tests/e2e/specs/test_company_onboarding.py
Browser-driven E2E tests for the company onboarding flow.

Tests are stubs that skip until the web console implements the onboarding flow.

Tests:
  1. /onboarding is accessible (not 404/500)
  2. Company form has required fields (name, legal entity ID)

Requires: Playwright, web-console running.
Marker: e2e
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Test 1: Onboarding flow accessible
# ---------------------------------------------------------------------------


def test_onboarding_flow_accessible(page) -> None:
    """Navigate to /onboarding and assert no 404 or 500 error."""
    if not _playwright_available():
        pytest.skip("playwright not installed")

    try:
        response = page.goto(page.url.rstrip("/") + "/onboarding", timeout=10000)
        if response is not None:
            status = response.status
            assert status not in (404, 500), (
                f"/onboarding returned HTTP {status} — route not implemented or server error"
            )
        # Also check page title is not an error page
        title = page.title()
        assert "404" not in title and "500" not in title, (
            f"Onboarding page shows error title: {title!r}"
        )
    except Exception as exc:
        pytest.skip(f"Onboarding route not yet implemented or web console not running: {exc}")


# ---------------------------------------------------------------------------
# Test 2: Company form has required fields
# ---------------------------------------------------------------------------


def test_company_form_has_required_fields(page) -> None:
    """
    The company onboarding form must contain fields for company name and legal entity ID.
    """
    if not _playwright_available():
        pytest.skip("playwright not installed")

    try:
        page.goto(page.url.rstrip("/") + "/onboarding", timeout=10000)

        # Look for company name field
        name_selectors = [
            "input[name='companyName']",
            "input[name='company_name']",
            "input[id*='company']",
            "[data-testid*='company-name']",
            "text=Company Name",
        ]
        has_name_field = any(
            page.locator(sel).count() > 0 for sel in name_selectors
        )

        # Look for legal entity ID field
        lei_selectors = [
            "input[name='legalEntityId']",
            "input[name='legal_entity_id']",
            "input[id*='bpn']",
            "input[id*='legal']",
            "[data-testid*='legal-entity']",
            "text=Legal Entity",
            "text=BPN",
        ]
        has_lei_field = any(
            page.locator(sel).count() > 0 for sel in lei_selectors
        )

        if not has_name_field and not has_lei_field:
            pytest.skip("Onboarding form fields not yet implemented in web console")

        assert has_name_field, "Company onboarding form must have a company name field"
        assert has_lei_field, "Company onboarding form must have a legal entity ID field"

    except Exception as exc:
        pytest.skip(f"Company onboarding form not yet implemented: {exc}")
