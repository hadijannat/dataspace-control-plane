"""
Browser-driven E2E tests for the operator login flow.

These tests target the actual web-console -> Keycloak Authorization Code + PKCE path.
"""
from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.e2e


def _playwright_api():
    return pytest.importorskip("playwright.sync_api", reason="pytest-playwright is required")


def _username_field(page):
    field = page.get_by_label(re.compile("Username", re.I))
    if field.count() == 0:
        field = page.locator("input[name='username']")
    return field


def _password_field(page):
    field = page.get_by_label(re.compile("Password", re.I))
    if field.count() == 0:
        field = page.locator("input[type='password']")
    return field


def _submit_button(page):
    button = page.get_by_role("button", name=re.compile("sign in|log in", re.I))
    if button.count() == 0:
        button = page.locator("button[type='submit']")
    return button


def test_login_redirects_to_keycloak(page, web_console_url, keycloak_browser_client) -> None:
    """Opening the web console must redirect unauthenticated users to the Keycloak login page."""
    playwright = _playwright_api()
    expect = playwright.expect

    page.goto(web_console_url, wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r".*/protocol/openid-connect/auth.*"))
    expect(_username_field(page)).to_be_visible()
    expect(_password_field(page)).to_be_visible()


def test_login_with_valid_credentials(page, web_console_url, keycloak_operator_user) -> None:
    """Valid Keycloak credentials must land the operator on the dashboard."""
    playwright = _playwright_api()
    expect = playwright.expect

    page.goto(web_console_url, wait_until="domcontentloaded")
    expect(_username_field(page)).to_be_visible()

    _username_field(page).fill(keycloak_operator_user["username"])
    _password_field(page).fill(keycloak_operator_user["password"])
    _submit_button(page).click()

    expect(page).to_have_url(re.compile(r".*/dashboard(?:[/?#].*)?$"))
    expect(page.get_by_role("heading", name=re.compile("Dashboard", re.I))).to_be_visible()
    expect(page.get_by_role("link", name=re.compile("Tenants", re.I))).to_be_visible()


def test_login_with_invalid_credentials_shows_error(page, web_console_url) -> None:
    """Invalid credentials must keep the user on the Keycloak login page and show an error."""
    playwright = _playwright_api()
    expect = playwright.expect

    page.goto(web_console_url, wait_until="domcontentloaded")
    expect(_username_field(page)).to_be_visible()

    _username_field(page).fill("invalid_user@nowhere.test")
    _password_field(page).fill("definitely-wrong-password-xyz")
    _submit_button(page).click()

    expect(page).to_have_url(re.compile(r".*/login-actions/authenticate.*|.*/protocol/openid-connect/auth.*"))
    expect(page.get_by_text(re.compile("invalid username or password|invalid user|try again", re.I))).to_be_visible()
