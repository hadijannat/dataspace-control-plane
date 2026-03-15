"""DCP Issuer Service API client.

Implements the DCP Issuer Service REST surface for requesting credential
issuance and polling issuance status.

Endpoints:
- POST /issue          — request credential issuance
- GET  /issue/{id}     — poll issuance request status
"""
from __future__ import annotations

import logging
from typing import Any

from ..._shared.auth import TokenProvider
from ..._shared.http import AsyncAdapterClient
from ..._shared.retries import retry_transient_short
from .errors import DcpCredentialError

logger = logging.getLogger(__name__)


class DcpIssuerClient:
    """REST client for the DCP Issuer Service API.

    Responsible only for network I/O and response normalization. Business
    decisions about which credentials to request belong in procedures/.

    Usage::
        async with DcpIssuerClient(cfg, token_provider) as client:
            vc_jwt = await client.issue_credential(
                subject_did="did:web:subject.example.com",
                credential_type="MembershipCredential",
                claims={"memberOf": "did:web:org.example.com"},
            )
    """

    def __init__(
        self,
        issuer_service_url: str,
        token_provider: TokenProvider | None = None,
        *,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = issuer_service_url.rstrip("/")
        self._token_provider = token_provider
        self._timeout = timeout
        self._http: AsyncAdapterClient | None = None

    async def __aenter__(self) -> "DcpIssuerClient":
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
    async def issue_credential(
        self,
        subject_did: str,
        credential_type: str,
        claims: dict[str, Any],
    ) -> str:
        """Request the issuer to produce a VC JWT for the given subject.

        Args:
            subject_did: The DID of the credential subject.
            credential_type: The VC type label (e.g. "MembershipCredential").
            claims: Additional claim key/value pairs to embed in the VC.

        Returns:
            The issued VC as a compact JWT string.

        Raises:
            DcpCredentialError: If the issuer rejects or fails the request.
        """
        assert self._http is not None, "Use DcpIssuerClient as async context manager"
        body = {
            "subjectDid": subject_did,
            "credentialType": credential_type,
            "claims": claims,
        }
        try:
            resp = await self._http.post("/issue", json=body)
        except Exception as exc:
            raise DcpCredentialError(
                f"Credential issuance for subject {subject_did!r} type {credential_type!r} failed: {exc}"
            ) from exc

        data = resp.json()
        # Issuer service returns {"credential": "<vc_jwt>"} or the raw JWT string.
        if isinstance(data, dict):
            vc_jwt: str = data.get("credential") or data.get("vc") or data.get("token", "")
        else:
            vc_jwt = str(data)

        if not vc_jwt:
            raise DcpCredentialError(
                f"Issuer returned empty credential for subject {subject_did!r}"
            )
        logger.debug(
            "Credential issued: subject=%s type=%s", subject_did, credential_type
        )
        return vc_jwt

    @retry_transient_short
    async def get_issuance_status(self, request_id: str) -> dict[str, Any]:
        """Poll the status of an async issuance request.

        Args:
            request_id: The issuance request ID returned by a prior issue call.

        Returns:
            A dict with at least ``{"status": str, "requestId": str}``.
            Possible statuses: "PENDING", "ISSUED", "FAILED".

        Raises:
            DcpCredentialError: If the status endpoint returns an error.
        """
        assert self._http is not None, "Use DcpIssuerClient as async context manager"
        try:
            resp = await self._http.get(f"/issue/{request_id}")
        except Exception as exc:
            raise DcpCredentialError(
                f"Fetching issuance status for request {request_id!r} failed: {exc}"
            ) from exc
        result: dict[str, Any] = resp.json()
        logger.debug("Issuance status for %s: %s", request_id, result.get("status"))
        return result
