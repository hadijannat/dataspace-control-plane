"""Translates Gaia-X VC vocabulary into canonical dicts.

Gaia-X uses linked-data VCs with specific @type vocabulary.
This module normalizes them into plain canonical dicts.

Rules:
- Do NOT turn Gaia-X vocab into global core types.
- Return plain Python dicts only.
- No policy evaluation here.
"""
from __future__ import annotations


def translate_participant_credential(vc: dict) -> dict:
    """Extract canonical identity fields from a Gaia-X Participant VC.

    Gaia-X Participant VCs contain legal name, address, and registration number.

    Args:
        vc: Raw Gaia-X Verifiable Credential (JSON-LD dict or decoded JWT payload).

    Returns:
        Canonical dict with keys: legal_entity_id, legal_name, legal_address,
        registration_number, issuer_did.
    """
    cs = vc.get("credentialSubject") or {}
    # GX-23 vocabulary: gx:legalName, gx:headquarterAddress, gx:legalRegistrationNumber
    legal_name = (
        cs.get("gx:legalName")
        or cs.get("legalName")
        or cs.get("name")
        or ""
    )
    address = cs.get("gx:headquarterAddress") or cs.get("headquarterAddress") or {}
    if isinstance(address, dict):
        address_str = address.get("gx:countryCode") or address.get("countryCode") or str(address)
    else:
        address_str = str(address)

    reg_number = (
        cs.get("gx:legalRegistrationNumber")
        or cs.get("legalRegistrationNumber")
        or {}
    )
    if isinstance(reg_number, dict):
        reg_number_str = (
            reg_number.get("gx:vatID")
            or reg_number.get("gx:EORI")
            or reg_number.get("gx:leiCode")
            or str(reg_number)
        )
    else:
        reg_number_str = str(reg_number)

    subject_id = cs.get("id") or cs.get("@id") or ""
    issuer = vc.get("issuer") or vc.get("iss") or ""

    return {
        "legal_entity_id": subject_id,
        "legal_name": legal_name,
        "legal_address": address_str,
        "registration_number": reg_number_str,
        "issuer_did": issuer if isinstance(issuer, str) else issuer.get("id", ""),
    }


def translate_compliance_credential(vc: dict) -> dict:
    """Extract canonical compliance fields from a Gaia-X Compliance Credential VC.

    Args:
        vc: Raw Gaia-X Compliance Credential (JSON-LD dict or decoded JWT payload).

    Returns:
        Canonical dict with keys: issuer_did, issued_at, compliant, federation_id.
    """
    cs = vc.get("credentialSubject") or {}
    issuer = vc.get("issuer") or vc.get("iss") or ""
    issued_at = vc.get("issuanceDate") or vc.get("iat") or ""
    integrity = cs.get("gx:integrity") or cs.get("integrity") or {}
    compliant = bool(integrity) or cs.get("gx:compliant", False)
    federation_id = cs.get("gx:federationId") or cs.get("federationId") or ""

    return {
        "issuer_did": issuer if isinstance(issuer, str) else issuer.get("id", ""),
        "issued_at": str(issued_at),
        "compliant": compliant,
        "federation_id": federation_id,
    }
