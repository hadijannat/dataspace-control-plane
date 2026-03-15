"""DCP Credential Service API client.

Implements the DCP Credential Service REST surface as specified in the
Dataspace Credential Protocol 1.0 specification.

Endpoints:
- POST /credentials  — request a credential
- GET  /credentials  — list credentials for a subject DID

Authentication uses a DCP Self-Issued Identity token injected via the
provided TokenProvider.
"""
from __future__ import annotations

import logging
from typing import Any

from ..._shared.auth import TokenProvider
from ..._shared.http import AsyncAdapterClient
from ..._shared.retries import retry_transient_short
from .errors import DcpCredentialError

logger = logging.getLogger(__name__)


class DcpCredentialServiceClient:
    """REST client for the DCP Credential Service API.

    The client expects a ``token_provider`` that yields a valid SI token
    JWT for each request. Token acquisition and refresh are the caller's
    responsibility.

    Usage::
        async with DcpCredentialServiceClient(cfg, token_provider) as client:
            vc = await client.request_credential("MembershipCredential", vp_dict)
    """

    def __init__(
        self,
        credential_service_url: str,
        token_provider: TokenProvider | None = None,
        *,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = credential_service_url.rstrip("/")
        self._token_provider = token_provider
        self._timeout = timeout
        self._http: AsyncAdapterClient | None = None

    async def __aenter__(self) -> "DcpCredentialServiceClient":
        self._http = AsyncAdapterClient(
            self._base_url,
            self._token_provider,
            timeout=self._timeout,
        )
        await self._http.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._http:
            await self._http.__aexit__(*args)

    @retry_transient_short
    async def request_credential(
        self,
        credential_type: str,
        presentation: dict[str, Any],
    ) -> dict[str, Any]:
        """Request a credential from the DCP Credential Service.

        Sends a POST /credentials request with the credential type and a
        Verifiable Presentation proving the caller's identity.

        Args:
            credential_type: The requested VC type label (e.g. "MembershipCredential").
            presentation: A DCP-format Verifiable Presentation dict.

        Returns:
            The issued credential as a raw dict (VC JWT or JSON-LD shape).

        Raises:
            DcpCredentialError: If the service rejects the request.
        """
        assert self._http is not None, "Use DcpCredentialServiceClient as async context manager"
        body = {
            "credentialType": credential_type,
            "presentation": presentation,
        }
        try:
            resp = await self._http.post("/credentials", json=body)
        except Exception as exc:
            raise DcpCredentialError(
                f"Credential request for type {credential_type!r} failed: {exc}"
            ) from exc
        result: dict[str, Any] = resp.json()
        logger.debug(
            "Credential requested: type=%s status=%s",
            credential_type,
            resp.status_code,
        )
        return result

    @retry_transient_short
    async def list_credentials(self, subject_did: str) -> list[dict[str, Any]]:
        """List credentials associated with a subject DID.

        Args:
            subject_did: The DID whose credentials should be returned.

        Returns:
            A list of raw credential dicts.

        Raises:
            DcpCredentialError: If the service returns an unexpected error.
        """
        assert self._http is not None, "Use DcpCredentialServiceClient as async context manager"
        try:
            resp = await self._http.get("/credentials", params={"subject": subject_did})
        except Exception as exc:
            raise DcpCredentialError(
                f"Listing credentials for subject {subject_did!r} failed: {exc}"
            ) from exc
        result: list[dict[str, Any]] = resp.json()
        logger.debug(
            "Listed %d credentials for subject=%s", len(result), subject_did
        )
        return result
