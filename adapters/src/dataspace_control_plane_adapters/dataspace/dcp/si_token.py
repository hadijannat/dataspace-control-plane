"""Self-Issued Identity (SI) token handling for the DCP protocol (DCP spec §3).

DCP requires parties to prove identity with a signed JWT before credential
exchange. The JWT follows the Self-Issued OpenID Provider (SIOP) pattern
adapted for DCP: issuer and subject are both set to the caller's DID, and
the token is signed using a key referenced by key_id via the SignerPort.

No private key material is held here. All signing is delegated to the
SignerPort implementation (typically VaultTransitSigner).
"""
from __future__ import annotations

import base64
import json
import logging
import time
from typing import TYPE_CHECKING, Any

from .errors import DcpTokenError

if TYPE_CHECKING:
    from dataspace_control_plane_core.domains.machine_trust.ports import SignerPort

logger = logging.getLogger(__name__)

_JWT_HEADER_BASE = {"alg": "EdDSA", "typ": "JWT"}


def _b64url_encode(data: bytes) -> str:
    """Base64URL-encode bytes without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Base64URL-decode a string, tolerating missing padding."""
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


class SiTokenBuilder:
    """Builds a DCP Self-Issued Identity JWT.

    The token structure follows DCP spec §3:
    - ``iss``: the subject DID (self-issued — issuer == subject)
    - ``sub``: the subject DID
    - ``aud``: intended audience DID or service URL
    - ``iat``: issued-at (seconds since epoch)
    - ``exp``: expiry (iat + ttl_seconds)
    - Additional ``claims`` are merged into the payload.

    Signing is delegated to the provided ``SignerPort`` implementation.
    The ``key_id`` identifies the key within the signer's key store (e.g. Vault
    Transit key name).
    """

    def __init__(self, key_id: str, ttl_seconds: int = 300) -> None:
        self._key_id = key_id
        self._ttl = ttl_seconds

    async def build(
        self,
        subject_did: str,
        audience: str,
        claims: dict[str, Any],
        signer: "SignerPort",
    ) -> str:
        """Construct and sign a DCP SI token.

        Args:
            subject_did: The caller's DID. Used as both ``iss`` and ``sub``.
            audience: Target service URL or DID. Placed in ``aud``.
            claims: Additional claims merged into the JWT payload.
            signer: A SignerPort implementation (e.g. VaultTransitSigner).

        Returns:
            A compact JWS string (header.payload.signature).

        Raises:
            DcpTokenError: If signing fails or the signer returns unexpected output.
        """
        now = int(time.time())
        payload: dict[str, Any] = {
            "iss": subject_did,
            "sub": subject_did,
            "aud": audience,
            "iat": now,
            "exp": now + self._ttl,
            **claims,
        }

        header_json = json.dumps(_JWT_HEADER_BASE, separators=(",", ":")).encode()
        payload_json = json.dumps(payload, separators=(",", ":")).encode()

        header_b64 = _b64url_encode(header_json)
        payload_b64 = _b64url_encode(payload_json)
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

        try:
            sig_bytes = await signer.sign(signing_input, self._key_id)
        except Exception as exc:
            raise DcpTokenError(
                f"SI token signing failed for subject {subject_did!r}: {exc}"
            ) from exc

        sig_b64 = _b64url_encode(sig_bytes)
        token = f"{header_b64}.{payload_b64}.{sig_b64}"
        logger.debug("Built SI token for subject=%s audience=%s", subject_did, audience)
        return token


def decode_si_token(token: str) -> dict[str, Any]:
    """Decode a DCP SI token JWT without signature verification.

    Intended for inspection and logging only. Do NOT use for
    authorization decisions — always verify via DcpVerifierClient.

    Args:
        token: A compact JWS string (header.payload.signature).

    Returns:
        The decoded payload as a plain dict.

    Raises:
        DcpTokenError: If the token structure is malformed.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise DcpTokenError(f"Malformed SI token: expected 3 parts, got {len(parts)}")
    try:
        payload_bytes = _b64url_decode(parts[1])
        return json.loads(payload_bytes)
    except Exception as exc:
        raise DcpTokenError(f"Failed to decode SI token payload: {exc}") from exc
