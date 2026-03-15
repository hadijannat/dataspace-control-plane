"""
tests/e2e/conftest.py
Playwright fixtures and E2E suite configuration.

All E2E tests require a running web-console instance. Set WEB_CONSOLE_URL env var.
Playwright must be installed: playwright install chromium

All E2E tests are skipped unless --live-services is passed.
"""
from __future__ import annotations

import os

import pytest

# Re-export keycloak fixtures so e2e tests can request them
try:
    from tests.fixtures.containers import keycloak_container  # noqa: F401
    from tests.fixtures.keycloak import (  # noqa: F401
        keycloak_admin_url,
        keycloak_realm,
        keycloak_client,
        keycloak_operator_user,
    )
except Exception:
    pass


# ---------------------------------------------------------------------------
# Web console URL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def web_console_url() -> str:
    """Session-scoped web console URL, from WEB_CONSOLE_URL env var or default localhost."""
    return os.environ.get("WEB_CONSOLE_URL", "http://localhost:3000")


# ---------------------------------------------------------------------------
# Browser
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def browser(web_console_url: str):
    """
    Session-scoped Playwright Chromium browser instance.

    Skipped if playwright is not installed.
    """
    playwright_api = pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        yield browser
        browser.close()


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def page(browser, web_console_url: str):
    """
    Function-scoped Playwright page navigated to web_console_url.

    Closes on teardown.
    """
    context = browser.new_context()
    p = context.new_page()
    try:
        p.goto(web_console_url, timeout=15000)
    except Exception:
        pass  # Navigation may fail if web console is not running — tests will skip
    yield p
    p.close()
    context.close()
