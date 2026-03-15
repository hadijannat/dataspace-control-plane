"""
tests/e2e/conftest.py
Playwright fixtures and E2E suite configuration.

The suite prefers the official pytest-playwright plugin when available.
All E2E tests require --live-services and a running web-console instance.
"""
from __future__ import annotations

import importlib.util
import os

import pytest

_HAS_PYTEST_PLAYWRIGHT = importlib.util.find_spec("pytest_playwright") is not None


@pytest.fixture(scope="session")
def web_console_url() -> str:
    """Session-scoped web-console URL, from WEB_CONSOLE_URL env var or localhost."""
    return os.environ.get("WEB_CONSOLE_URL", "http://localhost:3000").rstrip("/")


@pytest.fixture(scope="session")
def base_url(web_console_url: str) -> str:
    """Base URL consumed by pytest-playwright when the plugin is installed."""
    return web_console_url


@pytest.fixture(scope="session")
def browser_context_args(playwright_artifacts_dir):
    """Store browser traces/screenshots under the repo-wide artifact directory."""
    return {
        "ignore_https_errors": True,
        "record_video_dir": str(playwright_artifacts_dir),
    }


if not _HAS_PYTEST_PLAYWRIGHT:
    @pytest.fixture(scope="function")
    def page():
        pytest.skip("pytest-playwright is not installed in this environment")
