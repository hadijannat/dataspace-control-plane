"""Shared async HTTP client wrapper used by all HTTP-based adapters.

All external HTTP calls go through this module. Concrete adapters build an
AsyncAdapterClient pointing at their base URL with their auth strategy.
"""
from __future__ import annotations

from typing import Any

import httpx

from .auth import TokenProvider
from .errors import (
    AdapterAuthError,
    AdapterConflictError,
    AdapterNotFoundError,
    AdapterTimeoutError,
    AdapterUnavailableError,
    AdapterValidationError,
)


class AsyncAdapterClient:
    """Thin async HTTP client with automatic auth injection and error mapping."""

    def __init__(
        self,
        base_url: str,
        token_provider: TokenProvider | None = None,
        *,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        verify: bool | str = True,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token_provider = token_provider
        self._timeout = timeout
        self._extra_headers = headers or {}
        self._verify = verify
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AsyncAdapterClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            verify=self._verify,
            headers=self._extra_headers,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _auth_headers(self) -> dict[str, str]:
        if self._token_provider is None:
            return {}
        token = await self._token_provider.get_token()
        return {"Authorization": f"Bearer {token}"}

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("DELETE", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        assert self._client is not None, "Use AsyncAdapterClient as an async context manager"
        auth = await self._auth_headers()
        headers = {**auth, **kwargs.pop("headers", {})}
        try:
            resp = await self._client.request(method, path, headers=headers, **kwargs)
        except httpx.TimeoutException as exc:
            raise AdapterTimeoutError(str(exc)) from exc
        except httpx.ConnectError as exc:
            raise AdapterUnavailableError(str(exc)) from exc
        _raise_for_status(resp)
        return resp


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    code = resp.status_code
    text = resp.text[:512]
    if code == 401:
        raise AdapterAuthError(f"HTTP 401: {text}", upstream_code=code)
    if code == 403:
        raise AdapterAuthError(f"HTTP 403: {text}", upstream_code=code)
    if code == 404:
        raise AdapterNotFoundError(f"HTTP 404: {text}", upstream_code=code)
    if code == 409:
        raise AdapterConflictError(f"HTTP 409: {text}", upstream_code=code)
    if code == 422:
        raise AdapterValidationError(f"HTTP 422: {text}", upstream_code=code)
    if code >= 500:
        raise AdapterUnavailableError(f"HTTP {code}: {text}", upstream_code=code)
    resp.raise_for_status()
