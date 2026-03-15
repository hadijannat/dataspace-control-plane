"""Keycloak Admin REST API client.

Wraps the Keycloak Admin REST API using ``AsyncAdapterClient`` (shared HTTP
client from ``_shared/http.py``) with client-credentials token injection.

Capabilities
------------
- List realm roles
- Get user by ID
- List user role-mappings
- Create a new OIDC client (returns client UUID)
- Assign roles to a user

All endpoints are under ``/admin/realms/{realm}/``.

Token acquisition
-----------------
The client obtains a service-account token (client_credentials grant) on first
use and caches it until ``exp - 30s``.  Tokens are never returned to callers.

Usage::

    async with KeycloakAdminClient(settings) as admin:
        roles = await admin.list_realm_roles()
        user  = await admin.get_user(user_id)
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from dataspace_control_plane_adapters._shared.http import AsyncAdapterClient
from dataspace_control_plane_adapters._shared.auth import TokenProvider
from dataspace_control_plane_adapters.infrastructure.keycloak.config import KeycloakSettings
from dataspace_control_plane_adapters.infrastructure.keycloak.errors import (
    KeycloakAdminError,
    KeycloakTokenInvalidError,
)

logger = logging.getLogger(__name__)


class _ClientCredentialsTokenProvider:
    """Obtains and caches a Keycloak service-account access token.

    Satisfies ``_shared/auth.py :: TokenProvider`` (structural subtyping).

    Tokens are obtained via the OAuth 2.0 client_credentials grant against the
    configured realm token endpoint.  The token is cached until 30 seconds
    before its ``expires_in`` lapses.

    Credentials are consumed here and never surfaced to callers.
    """

    def __init__(self, settings: KeycloakSettings) -> None:
        self._token_endpoint = settings.token_endpoint
        self._client_id = settings.admin_client_id
        self._client_secret = settings.client_secret.get_secret_value()
        self._cached_token: str | None = None
        self._expires_at: float = 0.0

    async def get_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        if self._cached_token and time.monotonic() < self._expires_at:
            return self._cached_token

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(
                    self._token_endpoint,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                    },
                )
            except httpx.RequestError as exc:
                raise KeycloakAdminError(
                    f"Failed to obtain admin token: {exc}"
                ) from exc

        if resp.status_code != 200:
            raise KeycloakTokenInvalidError(
                f"Token endpoint returned HTTP {resp.status_code}: {resp.text[:256]}"
            )

        data: dict = resp.json()
        self._cached_token = data["access_token"]
        # Cache with 30-second buffer before actual expiry.
        self._expires_at = time.monotonic() + float(data.get("expires_in", 60)) - 30
        logger.debug("Admin token refreshed, expires in ~%.0fs", data.get("expires_in", 60))
        return self._cached_token  # type: ignore[return-value]


class KeycloakAdminClient:
    """Keycloak Admin REST API wrapper.

    Uses ``AsyncAdapterClient`` for all HTTP calls with automatic bearer token
    injection from ``_ClientCredentialsTokenProvider``.

    Credentials are entirely contained within this class.  The token string
    is never returned from any method.

    Use as an async context manager::

        async with KeycloakAdminClient(settings) as client:
            roles = await client.list_realm_roles()
    """

    def __init__(self, settings: KeycloakSettings) -> None:
        self._settings = settings
        self._token_provider = _ClientCredentialsTokenProvider(settings)
        self._http: AsyncAdapterClient | None = None

    async def __aenter__(self) -> "KeycloakAdminClient":
        self._http = AsyncAdapterClient(
            base_url=self._settings.admin_base_url,
            token_provider=self._token_provider,
            timeout=30.0,
        )
        await self._http.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._http is not None:
            await self._http.__aexit__(*args)

    # ------------------------------------------------------------------
    # Realm roles
    # ------------------------------------------------------------------

    async def list_realm_roles(self) -> list[dict]:
        """Return all realm-level roles defined in the configured realm.

        Returns
        -------
        list[dict]
            Each dict has at least ``id``, ``name``, ``description``.
        """
        assert self._http is not None, "Use as async context manager"
        resp = await self._http.get("/roles")
        return resp.json()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    async def get_user(self, user_id: str) -> dict:
        """Fetch a Keycloak user representation by its internal UUID.

        Parameters
        ----------
        user_id:
            Keycloak user UUID (the ``sub`` claim from an OIDC token).

        Returns
        -------
        dict
            Keycloak UserRepresentation dict.
        """
        assert self._http is not None
        resp = await self._http.get(f"/users/{user_id}")
        return resp.json()

    async def list_user_roles(self, user_id: str) -> list[dict]:
        """Return all effective realm roles for a user.

        Parameters
        ----------
        user_id:
            Keycloak user UUID.

        Returns
        -------
        list[dict]
            Each dict has ``name`` and ``id`` at minimum.
        """
        assert self._http is not None
        resp = await self._http.get(f"/users/{user_id}/role-mappings/realm/composite")
        return resp.json()

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------

    async def create_client(self, client_repr: dict) -> str:
        """Create a new OIDC client in the realm.

        Parameters
        ----------
        client_repr:
            Keycloak ClientRepresentation dict.  At minimum must contain
            ``clientId`` and ``protocol``.

        Returns
        -------
        str
            UUID of the newly created client (extracted from the ``Location``
            response header).
        """
        assert self._http is not None
        resp = await self._http.post("/clients", json=client_repr)
        location: str = resp.headers.get("Location", "")
        if location:
            return location.rstrip("/").rsplit("/", 1)[-1]
        # Fall back to fetching by clientId if Location header is absent.
        client_id_val = client_repr.get("clientId", "")
        search_resp = await self._http.get(
            "/clients", params={"clientId": client_id_val}
        )
        clients: list[dict] = search_resp.json()
        if clients:
            return clients[0]["id"]
        raise KeycloakAdminError(
            f"Could not determine UUID of newly created client {client_id_val!r}"
        )

    # ------------------------------------------------------------------
    # Role assignments
    # ------------------------------------------------------------------

    async def assign_roles(self, user_id: str, roles: list[str]) -> None:
        """Assign realm roles to a user by role name.

        Parameters
        ----------
        user_id:
            Keycloak user UUID.
        roles:
            List of realm role names to assign.

        Raises
        ------
        KeycloakAdminError
            If a role name cannot be resolved or the assignment fails.
        """
        assert self._http is not None

        # Resolve role names → RoleRepresentation objects (need id + name).
        all_roles = await self.list_realm_roles()
        role_map: dict[str, dict] = {r["name"]: r for r in all_roles}

        missing = [r for r in roles if r not in role_map]
        if missing:
            raise KeycloakAdminError(
                f"Role(s) not found in realm: {missing!r}"
            )

        role_representations = [role_map[r] for r in roles]
        await self._http.post(
            f"/users/{user_id}/role-mappings/realm",
            json=role_representations,
        )
