"""Catena-X credential profiles.

Defines the VC types required for Catena-X participation and provides
minimal VC payload builders for each credential type.

Reference: Catena-X Operating Model v4.0
"""
from __future__ import annotations

from typing import Any

MEMBERSHIP_CREDENTIAL = "MembershipCredential"
BPN_CREDENTIAL = "BpnCredential"
DATA_EXCHANGE_GOVERNANCE_CREDENTIAL = "DataExchangeGovernanceCredential"

_ALL_CREDENTIAL_TYPES: list[str] = [
    MEMBERSHIP_CREDENTIAL,
    BPN_CREDENTIAL,
    DATA_EXCHANGE_GOVERNANCE_CREDENTIAL,
]

_CONTEXT = [
    "https://www.w3.org/2018/credentials/v1",
    "https://w3id.org/catenax/credentials/v1",
]


class CatenaxCredentialProfileProvider:
    """CredentialProfileProvider for Catena-X verifiable credentials."""

    def required_credentials(self, *, context: dict[str, Any]) -> list[str]:
        """Return the list of required credential types for the given context.

        Rules:
        - All participants require MembershipCredential and BpnCredential.
        - Data-exchange contexts additionally require DataExchangeGovernanceCredential.
        """
        required = [MEMBERSHIP_CREDENTIAL, BPN_CREDENTIAL]

        purpose = context.get("purpose", "")
        operation = context.get("operation", "")
        if purpose or operation in ("data_exchange", "contract_negotiation", "publishing"):
            required.append(DATA_EXCHANGE_GOVERNANCE_CREDENTIAL)

        return required

    def build_vc_payload(
        self,
        credential_type: str,
        subject: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Build a minimal VC payload dict for ``credential_type``.

        The returned dict contains ``@context``, ``type``, ``credentialSubject``,
        and an ``issuer`` placeholder. It does not include a proof or issuance date —
        those are filled in by the issuing infrastructure.

        Raises:
            ValueError: If ``credential_type`` is not a known Catena-X credential type.
        """
        if credential_type not in _ALL_CREDENTIAL_TYPES:
            raise ValueError(
                f"Unknown Catena-X credential type: {credential_type!r}. "
                f"Known types: {_ALL_CREDENTIAL_TYPES}"
            )

        credential_subject = _build_credential_subject(credential_type, subject)

        return {
            "@context": _CONTEXT,
            "type": ["VerifiableCredential", credential_type],
            "issuer": "PLACEHOLDER_ISSUER_DID",
            "credentialSubject": credential_subject,
            "activation_scope": activation_scope,
        }


def _build_credential_subject(
    credential_type: str, subject: dict[str, Any]
) -> dict[str, Any]:
    """Build the credentialSubject block for the given credential type."""
    base: dict[str, Any] = {}

    if "id" in subject:
        base["id"] = subject["id"]
    elif "bpnl" in subject:
        base["id"] = f"did:bpnl:{subject['bpnl']}"

    if credential_type == MEMBERSHIP_CREDENTIAL:
        base["memberOf"] = "Catena-X"
        if "bpnl" in subject:
            base["bpnl"] = subject["bpnl"]

    elif credential_type == BPN_CREDENTIAL:
        for key in ("bpnl", "bpns", "bpna"):
            if key in subject:
                base[key] = subject[key]

    elif credential_type == DATA_EXCHANGE_GOVERNANCE_CREDENTIAL:
        base["degAccepted"] = subject.get("deg_accepted", False)
        if subject.get("deg_accepted_at"):
            base["degAcceptedAt"] = subject["deg_accepted_at"]
        if "bpnl" in subject:
            base["bpnl"] = subject["bpnl"]

    return base
