"""Gaia-X credential profile provider.

Maps canonical identity/credential models to Gaia-X VC structures using the
GX-23 vocabulary.  Implements :class:`CredentialProfileProvider`.

Normative reference: Gaia-X Trust Framework 22.10, §4 (Participant) and §5
(Service Offering, Data Resource).

No HTTP, DB, or Temporal code here.
"""
from __future__ import annotations

from typing import Any

from ..._shared.provenance import attach_module_provenance
from .trust_framework import GX_VOCABULARY_URI, GX_W3C_VC_CONTEXT

# ---------------------------------------------------------------------------
# Credential type registry (GX-23 vocabulary)
# ---------------------------------------------------------------------------

GX_CREDENTIAL_TYPES: dict[str, str] = {
    "participant": "gx:LegalParticipant",
    "service": "gx:ServiceOffering",
    "resource": "gx:DataResource",
}
"""Maps canonical subject type keys to Gaia-X GX-23 credential type names."""

# GX-23 vocabulary @context shorthand
_GX_CONTEXT_ENTRY = {"gx": GX_VOCABULARY_URI}

# Minimal field mapping from canonical subject to Gaia-X credential subject
_PARTICIPANT_FIELD_MAP: dict[str, str] = {
    "legal_name": "gx:legalName",
    "legal_registration_number": "gx:legalRegistrationNumber",
    "headquarter_address": "gx:headquarterAddress",
    "legal_address": "gx:legalAddress",
}

_SERVICE_FIELD_MAP: dict[str, str] = {
    "name": "gx:name",
    "description": "gx:description",
    "provided_by": "gx:providedBy",
    "aggregation_of": "gx:aggregationOf",
    "terms_and_conditions": "gx:termsAndConditions",
    "policy": "gx:policy",
}

_RESOURCE_FIELD_MAP: dict[str, str] = {
    "name": "gx:name",
    "description": "gx:description",
    "produced_by": "gx:producedBy",
    "exposed_through": "gx:exposedThrough",
    "license": "gx:license",
}

_FIELD_MAPS: dict[str, dict[str, str]] = {
    "participant": _PARTICIPANT_FIELD_MAP,
    "service": _SERVICE_FIELD_MAP,
    "resource": _RESOURCE_FIELD_MAP,
}
_CREDENTIAL_RULE_IDS = {
    "participant": ["gaia_x:gx23-legal-participant"],
    "service": ["gaia_x:gx23-service-offering"],
    "resource": ["gaia_x:gx23-data-resource"],
}


class GaiaXCredentialProfileProvider:
    """Maps canonical identity models to Gaia-X VC payloads.

    This is a baseline provider.  Federation-specific overlays may extend
    required credential sets or map additional fields.
    """

    # ------------------------------------------------------------------
    # CredentialProfileProvider interface
    # ------------------------------------------------------------------

    def required_credentials(self, *, context: dict[str, Any]) -> list[str]:
        """Return required credential type names for ``context``.

        The ``subject_type`` key in ``context`` determines which credential
        types are expected:
          - ``"participant"`` → ``["gx:LegalParticipant"]``
          - ``"service"``     → ``["gx:LegalParticipant", "gx:ServiceOffering"]``
          - ``"resource"``    → ``["gx:LegalParticipant", "gx:DataResource"]``
          - default           → all three types

        Returns a list of GX-23 type names (not canonical keys).
        """
        subject_type = context.get("subject_type", "")

        if subject_type == "participant":
            return [GX_CREDENTIAL_TYPES["participant"]]
        if subject_type == "service":
            return [
                GX_CREDENTIAL_TYPES["participant"],
                GX_CREDENTIAL_TYPES["service"],
            ]
        if subject_type == "resource":
            return [
                GX_CREDENTIAL_TYPES["participant"],
                GX_CREDENTIAL_TYPES["resource"],
            ]
        # Unknown or unset subject_type — return all three as a safe default
        return list(GX_CREDENTIAL_TYPES.values())

    def build_vc_payload(
        self,
        credential_type: str,
        subject: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Build a Gaia-X VC payload for ``credential_type`` from ``subject``.

        The payload uses the GX-23 vocabulary and W3C VC Data Model context.

        Args:
            credential_type:  A GX-23 type name (e.g. ``"gx:LegalParticipant"``)
                              or canonical key (e.g. ``"participant"``).
            subject:          Canonical subject dict.
            activation_scope: Tenant/scope identifier stamped on the payload.

        Returns:
            A VC payload dict (not signed — signing is an adapter concern).
        """
        # Resolve canonical key if a full GX type name is passed
        canonical_key = self._resolve_canonical_key(credential_type)
        gx_type = GX_CREDENTIAL_TYPES.get(canonical_key, credential_type)
        field_map = _FIELD_MAPS.get(canonical_key, {})

        credential_subject: dict[str, Any] = {}
        if "id" in subject:
            credential_subject["id"] = str(subject["id"])
        for canonical_field, gx_field in field_map.items():
            if canonical_field in subject:
                credential_subject[gx_field] = subject[canonical_field]

        payload: dict[str, Any] = {
            "@context": [GX_W3C_VC_CONTEXT, _GX_CONTEXT_ENTRY],
            "@type": ["VerifiableCredential", gx_type],
            "credentialSubject": credential_subject,
            # Non-normative metadata
            "_gx_pack_version": "22.10.0",
            "_gx_activation_scope": activation_scope,
        }
        return attach_module_provenance(
            payload,
            module_file=__file__,
            rule_ids=_CREDENTIAL_RULE_IDS.get(canonical_key, [gx_type]),
            activation_scope=activation_scope,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_canonical_key(credential_type: str) -> str:
        """Return canonical key for either a canonical key or GX type name."""
        # Passed directly as a canonical key
        if credential_type in GX_CREDENTIAL_TYPES:
            return credential_type
        # Passed as a GX type name — reverse lookup
        for key, gx_type in GX_CREDENTIAL_TYPES.items():
            if gx_type == credential_type:
                return key
        return credential_type
