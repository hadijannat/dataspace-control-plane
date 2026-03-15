"""Keycloak adapter-specific error hierarchy.

Rules:
- KeycloakError is the root for all Keycloak-layer exceptions.
- KeycloakTokenExpiredError is raised when JWT exp has passed.
- KeycloakTokenInvalidError is raised for signature failure, unknown kid, etc.
- All errors translate to AdapterAuthError at the port boundary.
"""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.errors import (
    AdapterAuthError,
    AdapterError,
)


class KeycloakError(AdapterError):
    """Root for all Keycloak adapter errors."""


class KeycloakTokenExpiredError(AdapterAuthError):
    """Raised when the OIDC access token has expired (JWT exp < now).

    Callers should refresh the token and retry.
    """

    def __init__(self, detail: str = "Access token has expired") -> None:
        super().__init__(detail, upstream_code="token_expired")


class KeycloakTokenInvalidError(AdapterAuthError):
    """Raised when the OIDC token fails signature verification, has invalid
    structure, or uses an unknown key identifier (kid).

    Callers should NOT retry — the token is invalid and must be discarded.
    """

    def __init__(self, detail: str = "Access token is invalid") -> None:
        super().__init__(detail, upstream_code="token_invalid")


class KeycloakJwksRefreshError(KeycloakError):
    """Raised when the JWKS endpoint is unreachable or returns a non-200 response."""


class KeycloakAdminError(KeycloakError):
    """Raised when the Admin REST API call fails."""
