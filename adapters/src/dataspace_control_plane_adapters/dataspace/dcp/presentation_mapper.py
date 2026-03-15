"""DCP presentation mapper.

Translates raw DCP presentation dicts into canonical dict shapes consumed by
``ports_impl.py``. Verification responses are normalized into the core
``VerificationResult`` enum so the adapter boundary does not leak DCP-specific
response keys such as ``valid`` or ``holderDid``.
"""
from __future__ import annotations

from typing import Any

from dataspace_control_plane_core.domains.machine_trust.model.enums import (
    VerificationResult,
)


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


def map_verification_result(raw_result: dict[str, Any]) -> VerificationResult:
    """Normalize a raw DCP verifier response to the core ``VerificationResult`` enum."""
    if bool(raw_result.get("valid", False)):
        return VerificationResult.VALID

    error_text = str(
        raw_result.get("error")
        or raw_result.get("errorMessage")
        or raw_result.get("status")
        or ""
    ).strip().lower()

    if "signature" in error_text:
        return VerificationResult.INVALID_SIGNATURE
    if "revok" in error_text:
        return VerificationResult.REVOKED
    if "expir" in error_text:
        return VerificationResult.EXPIRED
    if "trust" in error_text or "issuer" in error_text or "anchor" in error_text:
        return VerificationResult.UNTRUSTED_ISSUER

    return VerificationResult.UNKNOWN


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
