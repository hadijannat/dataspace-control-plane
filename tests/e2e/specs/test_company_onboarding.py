"""
Placeholder E2E spec for company onboarding.

The current web-console does not expose an onboarding route, so this remains an
explicit dependency note for the apps/ owner rather than a silent skip.
"""
from __future__ import annotations

import re

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.xfail(
        reason="Dependency on apps/web-console: onboarding route is not implemented yet",
        strict=False,
    ),
]


def test_onboarding_route_exists(page, web_console_url) -> None:
    playwright = pytest.importorskip("playwright.sync_api", reason="pytest-playwright is required")
    expect = playwright.expect

    page.goto(f"{web_console_url}/onboarding", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r".*/onboarding(?:[/?#].*)?$"))
