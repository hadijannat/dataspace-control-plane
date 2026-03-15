"""DCP presentation mapper.

Translates raw DCP presentation and verification result dicts into
canonical dict shapes consumed by ports_impl.py. No core domain types
are imported here — output is plain dicts to avoid creating import chains
between the adapter and the core at this layer.

The canonical presentation dict shape mirrors PresentationEnvelope fields
but as plain Python dicts (serialization-safe).
"""
from __future__ import annotations

from typing import Any


def map_presentation(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw DCP presentation dict to a canonical presentation dict.

    The DCP wire format uses camelCase keys. This function produces a
    snake_case canonical dict matching the PresentationEnvelope schema::

        {
            "id": str,
            "holder_did": str,
            "credentials": list[dict],
            "created_at": str | None,   # ISO 8601
            "challenge": str | None,
            "domain": str | None,
        }

    Args:
        raw: Raw presentation dict from the DCP Credential Service or VP JWT payload.

    Returns:
        Canonical presentation dict (plain dict, not a domain type).
    """
    credentials_raw: list[Any] = (
        raw.get("verifiableCredential")
        or raw.get("credentials")
        or raw.get("vcs")
        or []
    )
    canonical_credentials = [map_vc_to_credential_dict(c) for c in credentials_raw]

    return {
        "id": raw.get("id") or raw.get("jti") or "",
        "holder_did": (
            raw.get("holderDid")
            or raw.get("holder_did")
            or raw.get("holder")
            or raw.get("iss")
            or ""
        ),
        "credentials": canonical_credentials,
        "created_at": raw.get("created") or raw.get("iat") or None,
        "challenge": raw.get("nonce") or raw.get("challenge") or None,
        "domain": raw.get("domain") or None,
    }


def map_verification_result(raw_result: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw DCP verifier response to a canonical verification result dict.

    Output shape::

        {
            "valid": bool,
            "holder_did": str | None,
            "credentials": list[dict],
            "error": str | None,
        }

    Args:
        raw_result: Raw dict from DcpVerifierClient.verify_presentation().

    Returns:
        Canonical verification result dict (plain dict).
    """
    return {
        "valid": bool(raw_result.get("valid", False)),
        "holder_did": (
            raw_result.get("holder_did")
            or raw_result.get("holderDid")
            or None
        ),
        "credentials": raw_result.get("credentials") or [],
        "error": raw_result.get("error") or None,
    }


def map_vc_to_credential_dict(raw_vc: Any) -> dict[str, Any]:
    """Normalize a single raw VC (JWT string or JSON-LD dict) to a credential dict.

    For JWT VCs the payload is extracted without verification (use verifier
    for trust decisions). For JSON-LD VCs the structure is normalised.

    Args:
        raw_vc: Either a compact JWT string or a JSON-LD VC dict.

    Returns:
        A flat canonical credential dict suitable for embedding in a presentation.
    """
    if isinstance(raw_vc, str):
        # Compact JWT VC — decode payload segment for field extraction.
        from .credential_mapper import map_vc_jwt
        return map_vc_jwt(raw_vc)

    if isinstance(raw_vc, dict):
        # JSON-LD VC
        cs = raw_vc.get("credentialSubject") or {}
        return {
            "id": raw_vc.get("id") or "",
            "issuer_did": raw_vc.get("issuer") or "",
            "subject_did": cs.get("id") or "",
            "type_labels": raw_vc.get("type") or [],
            "issued_at": raw_vc.get("issuanceDate") or None,
            "expires_at": raw_vc.get("expirationDate") or None,
            "claims": {k: v for k, v in cs.items() if k != "id"},
        }

    # Unknown shape — return minimal dict.
    return {"raw": raw_vc}
