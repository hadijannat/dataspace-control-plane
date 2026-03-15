"""DCP Verifier Service API client.

Wraps the DCP Verifier REST endpoint. Returns raw verification result dicts
that are subsequently normalized by presentation_mapper.py.

Endpoint:
- POST /verify  — verify a Verifiable Presentation JWT
"""
from __future__ import annotations

import logging
from typing import Any

from ..._shared.auth import TokenProvider
from ..._shared.http import AsyncAdapterClient
from ..._shared.retries import retry_transient_short
from .errors import DcpVerificationError

logger = logging.getLogger(__name__)


class DcpVerifierClient:
    """REST client for the DCP Verifier API.

    The verifier checks that:
    1. The presentation JWT is well-formed and cryptographically valid.
    2. All embedded credentials match the required type labels.
    3. The holder DID is the subject of every embedded credential.

    This client normalizes raw HTTP responses into dicts. Canonical type
    mapping is done by presentation_mapper.py.

    Usage::
        async with DcpVerifierClient(verifier_url) as client:
            result = await client.verify_presentation(vp_jwt, ["MembershipCredential"])
    """

    def __init__(
        self,
        verifier_url: str,
        token_provider: TokenProvider | None = None,
        *,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = verifier_url.rstrip("/")
        self._token_provider = token_provider
        self._timeout = timeout
        self._http: AsyncAdapterClient | None = None

    async def __aenter__(self) -> "DcpVerifierClient":
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
    async def verify_presentation(
        self,
        presentation_jwt: str,
        required_types: list[str],
    ) -> dict[str, Any]:
        """Verify a Verifiable Presentation JWT against required credential types.

        Args:
            presentation_jwt: Compact JWS string encoding the VP.
            required_types: List of VC type labels that must be present and valid.

        Returns:
            A dict with the following shape::

                {
                    "valid": bool,
                    "holder_did": str | None,
                    "credentials": list[dict],  # raw VC claims per credential
                    "error": str | None,
                }

        Raises:
            DcpVerificationError: If the verifier endpoint is unavailable or
                returns a non-HTTP-error structural failure.
        """
        assert self._http is not None, "Use DcpVerifierClient as async context manager"
        body = {
            "presentation": presentation_jwt,
            "requiredCredentialTypes": required_types,
        }
        try:
            resp = await self._http.post("/verify", json=body)
        except Exception as exc:
            raise DcpVerificationError(
                f"Verification call failed for required types {required_types}: {exc}"
            ) from exc

        data: dict[str, Any] = resp.json()

        # Normalize to a stable dict shape regardless of remote service version.
        result: dict[str, Any] = {
            "valid": bool(data.get("valid", False)),
            "holder_did": data.get("holderDid") or data.get("holder_did"),
            "credentials": data.get("credentials") or data.get("vcs") or [],
            "error": data.get("error") or data.get("errorMessage"),
        }
        logger.debug(
            "Verification result: valid=%s holder=%s",
            result["valid"],
            result["holder_did"],
        )
        return result
