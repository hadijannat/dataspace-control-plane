"""Teamcenter REST client with session-based authentication."""
from __future__ import annotations

from typing import Any

import httpx

from ..._shared.http import AsyncAdapterClient
from .config import TeamcenterSettings
from .errors import TeamcenterAuthError, TeamcenterError


_LOGIN_PATH = "/tc/micro/ServiceRegistry/SessionService/login"


class TeamcenterClient:
    """Teamcenter REST client that uses session-based auth.

    Authentication is performed via POST to the SessionService login endpoint.
    The returned session cookie/token is stored and injected into subsequent
    requests automatically via the underlying AsyncAdapterClient.

    Usage::

        client = TeamcenterClient(settings)
        await client.login()
        data = await client.get("/tc/micro/ItemService/Item/ABC123")
    """

    def __init__(self, settings: TeamcenterSettings) -> None:
        self._settings = settings
        self._session_token: str | None = None
        self._base_url = str(settings.base_url).rstrip("/")

    async def login(self) -> None:
        """Authenticate against Teamcenter and cache the session token.

        Raises TeamcenterAuthError on credential rejection or network failures.
        """
        body = {
            "username": self._settings.username,
            "password": self._settings.password.get_secret_value(),
        }
        try:
            async with httpx.AsyncClient(timeout=30.0, base_url=self._base_url) as client:
                resp = await client.post(
                    _LOGIN_PATH,
                    json=body,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code in (401, 403):
                    raise TeamcenterAuthError(
                        f"Teamcenter login rejected (HTTP {resp.status_code}).",
                        upstream_code=resp.status_code,
                    )
                resp.raise_for_status()
                payload = resp.json()
                # Token may be in the response body or a Set-Cookie header.
                self._session_token = (
                    payload.get("sessionDiscriminator")
                    or payload.get("token")
                    or resp.cookies.get("JSESSIONID")
                )
        except TeamcenterAuthError:
            raise
        except Exception as exc:
            raise TeamcenterAuthError(
                f"Teamcenter login failed: {exc}"
            ) from exc

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Execute an authenticated GET request and return the parsed JSON body."""
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Execute an authenticated POST request and return the parsed JSON body."""
        return await self._request("POST", path, json=body)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        """Return session auth headers for Teamcenter requests."""
        if self._session_token:
            return {"X-TC-Session": self._session_token}
        return {}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if self._session_token is None:
            raise TeamcenterError(
                "Not authenticated. Call login() before making requests."
            )
        headers = {**self._auth_headers(), **kwargs.pop("headers", {})}
        try:
            async with httpx.AsyncClient(
                timeout=60.0,
                base_url=self._base_url,
            ) as client:
                resp = await client.request(method, path, headers=headers, **kwargs)
                if resp.status_code in (401, 403):
                    raise TeamcenterAuthError(
                        f"Teamcenter request unauthorised (HTTP {resp.status_code}): {path}",
                        upstream_code=resp.status_code,
                    )
                resp.raise_for_status()
                return resp.json()  # type: ignore[return-value]
        except TeamcenterAuthError:
            raise
        except httpx.HTTPStatusError as exc:
            raise TeamcenterError(
                f"Teamcenter HTTP {exc.response.status_code} for {path}",
                upstream_code=exc.response.status_code,
            ) from exc
        except Exception as exc:
            raise TeamcenterError(f"Teamcenter request error for {path}: {exc}") from exc
