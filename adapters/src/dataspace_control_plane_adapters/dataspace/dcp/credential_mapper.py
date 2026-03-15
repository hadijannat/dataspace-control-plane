"""DCP credential mapper.

Translates raw VC JWT strings and JSON-LD VC dicts into canonical
identity-oriented dicts. No verification is performed here — this module
only normalizes structure. Trust decisions belong in the Verifier path.

Output shapes are plain dicts (not core domain types) to keep the adapter
wire-model local to this package.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _b64url_decode_segment(segment: str) -> bytes:
    """Base64URL-decode a JWT segment, tolerating missing padding."""
    pad = 4 - len(segment) % 4
    if pad != 4:
        segment += "=" * pad
    return base64.urlsafe_b64decode(segment)


def map_vc_jwt(vc_jwt: str) -> dict[str, Any]:
    """Decode a compact VC JWT and return a normalised credential dict.

    Does NOT verify the signature. Use DcpVerifierClient for trust decisions.

    JWT payload fields mapped:
    - ``iss``         → ``issuer_did``
    - ``sub``         → ``subject_did``
    - ``jti``         → ``id``
    - ``iat``         → ``issued_at``
    - ``exp``         → ``expires_at``
    - ``vc.type``     → ``type_labels``
    - ``vc.credentialSubject`` → ``claims``

    Args:
        vc_jwt: Compact JWS string (header.payload.signature).

    Returns:
        Canonical credential dict.
    """
    parts = vc_jwt.split(".")
    if len(parts) != 3:
        logger.warning("Received malformed VC JWT (expected 3 parts, got %d)", len(parts))
        return {"raw_jwt": vc_jwt, "parse_error": "malformed_jwt"}

    try:
        payload_bytes = _b64url_decode_segment(parts[1])
        payload: dict[str, Any] = json.loads(payload_bytes)
    except Exception as exc:
        logger.warning("Failed to decode VC JWT payload: %s", exc)
        return {"raw_jwt": vc_jwt, "parse_error": str(exc)}

    vc_block: dict[str, Any] = payload.get("vc") or {}
    credential_subject: dict[str, Any] = vc_block.get("credentialSubject") or {}

    return {
        "id": payload.get("jti") or vc_block.get("id") or "",
        "issuer_did": payload.get("iss") or vc_block.get("issuer") or "",
        "subject_did": (
            payload.get("sub")
            or credential_subject.get("id")
            or ""
        ),
        "type_labels": vc_block.get("type") or [],
        "issued_at": payload.get("iat"),
        "expires_at": payload.get("exp"),
        "claims": {k: v for k, v in credential_subject.items() if k != "id"},
        "format": "jwt_vc",
    }


def map_vc_claims_to_identity(claims: dict[str, Any]) -> dict[str, Any]:
    """Extract identity-relevant fields from decoded VC claims.

    This function is applied to the ``claims`` dict produced by map_vc_jwt()
    or to the ``credentialSubject`` dict from a JSON-LD VC.

    Output shape::

        {
            "subject_did": str,
            "issuer_did": str,
            "type_labels": list[str],
            "legal_name": str | None,
            "registration_number": str | None,
        }

    No Gaia-X or Catena-X vocabulary logic here — that belongs in
    dataspace/gaiax/credential_translation.py or packs/.

    Args:
        claims: Credential claims dict (from credentialSubject or decoded JWT).

    Returns:
        Normalised identity dict (plain dict).
    """
    return {
        "subject_did": claims.get("id") or claims.get("subject_did") or "",
        "issuer_did": claims.get("issuer_did") or "",
        "type_labels": claims.get("type_labels") or [],
        "legal_name": (
            claims.get("legalName")
            or claims.get("legal_name")
            or claims.get("name")
            or None
        ),
        "registration_number": (
            claims.get("registrationNumber")
            or claims.get("registration_number")
            or None
        ),
    }
