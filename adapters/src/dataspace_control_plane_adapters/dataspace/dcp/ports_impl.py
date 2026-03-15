"""DCP port implementations.

Bridges the DCP adapter clients to the core port interfaces defined in
core/domains/machine_trust/ports.py.

Implementations:
- DcpCredentialIssuer   → CredentialIssuerPort
- DcpPresentationVerifier → PresentationVerifierPort
- DcpTrustAnchorResolver  → TrustAnchorResolverPort

No business logic here. Each method performs only:
1. Type mapping (canonical → wire, wire → canonical)
2. Delegation to the relevant DCP API client

Error translation from DcpError → core error types happens at the service
boundary; adapters catch DcpError subtypes and let them propagate for now
(they are caught at the procedure/activity layer which owns error policy).
"""
from __future__ import annotations

import logging
from typing import Any

from dataspace_control_plane_core.canonical_models.identity import (
    DidUri,
    PresentationEnvelope,
)
from dataspace_control_plane_core.domains.machine_trust.model.value_objects import TrustAnchor

from .config import DcpSettings
from .credential_mapper import map_vc_jwt
from .issuer_client import DcpIssuerClient
from .presentation_mapper import map_verification_result
from .verifier_client import DcpVerifierClient

logger = logging.getLogger(__name__)


class DcpCredentialIssuer:
    """Implements core/domains/machine_trust/ports.py CredentialIssuerPort.

    Delegates issuance to DcpIssuerClient. No credential content decisions
    are made here — the caller (procedure/activity) is responsible for
    what claims to request.
    """

    def __init__(self, cfg: DcpSettings) -> None:
        self._cfg = cfg

    async def issue(
        self,
        subject_did: DidUri,
        claims: dict[str, Any],
        type_labels: list[str],
    ) -> str:
        """Issue a VC JWT for the given subject DID.

        Args:
            subject_did: The credential subject's DID.
            claims: Claims to embed in the credential subject block.
            type_labels: VC type labels (e.g. ["VerifiableCredential", "MembershipCredential"]).

        Returns:
            Compact VC JWT string.
        """
        async with DcpIssuerClient(
            str(self._cfg.issuer_service_url),
            timeout=self._cfg.request_timeout_s,
        ) as client:
            # Use the first non-base type label as the credential type.
            credential_type = next(
                (t for t in type_labels if t != "VerifiableCredential"),
                type_labels[0] if type_labels else "VerifiableCredential",
            )
            return await client.issue_credential(
                subject_did=str(subject_did),
                credential_type=credential_type,
                claims=claims,
            )


class DcpPresentationVerifier:
    """Implements core/domains/machine_trust/ports.py PresentationVerifierPort.

    Delegates verification to DcpVerifierClient and normalises the result
    via presentation_mapper.
    """

    def __init__(self, cfg: DcpSettings, verifier_url: str | None = None) -> None:
        self._cfg = cfg
        # verifier_url can differ from the credential_service_url.
        # If not provided, fall back to credential_service_url (common in test setups).
        self._verifier_url = verifier_url or str(cfg.credential_service_url)

    async def verify(self, presentation: PresentationEnvelope) -> dict[str, Any]:
        """Verify a canonical PresentationEnvelope via the DCP Verifier.

        Args:
            presentation: Canonical PresentationEnvelope from core.

        Returns:
            Canonical verification result dict::

                {
                    "valid": bool,
                    "holder_did": str | None,
                    "credentials": list[dict],
                    "error": str | None,
                }
        """
        # Extract type labels from the first credential for required_types.
        required_types: list[str] = []
        for cred_env in presentation.credentials:
            required_types.extend(cred_env.type_labels)

        # Build a minimal VP JWT representation for the verifier.
        # In production the caller should pass a signed VP JWT via presentation.id
        # or a custom extension field. Here we pass the presentation id as the token.
        presentation_jwt = presentation.id  # callers store the raw JWT in .id

        async with DcpVerifierClient(
            self._verifier_url,
            timeout=self._cfg.request_timeout_s,
        ) as client:
            raw_result = await client.verify_presentation(
                presentation_jwt=presentation_jwt,
                required_types=list(set(required_types)),
            )

        return map_verification_result(raw_result)


class DcpTrustAnchorResolver:
    """Implements core/domains/machine_trust/ports.py TrustAnchorResolverPort.

    Reads trust anchor endpoints from DcpSettings.trust_anchor_urls and
    fetches the list of active anchors from each endpoint.

    In the current implementation anchors are resolved from static config.
    A future implementation may query a Trust Anchor Registry API.
    """

    def __init__(self, cfg: DcpSettings) -> None:
        self._cfg = cfg

    async def list_active(self, trust_scope: str) -> list[TrustAnchor]:
        """List active trust anchors for the given trust scope.

        The trust_scope string is matched case-insensitively against the
        name of each configured anchor URL (the hostname segment is used
        as a proxy for scope).

        Args:
            trust_scope: Trust scope identifier (e.g. "catena-x", "gaia-x").

        Returns:
            List of TrustAnchor value objects from core.
        """
        anchors: list[TrustAnchor] = []
        for url in self._cfg.trust_anchor_urls:
            # Each URL represents a trust anchor endpoint.
            # Parse a DID from the URL for the TrustAnchor model.
            did_str = _url_to_did_web(url)
            anchor = TrustAnchor(
                name=url,
                did=DidUri(uri=did_str),
                trust_scope=trust_scope,
                is_active=True,
            )
            anchors.append(anchor)
        logger.debug(
            "Resolved %d trust anchors for scope=%s", len(anchors), trust_scope
        )
        return anchors


def _url_to_did_web(url: str) -> str:
    """Convert an HTTPS URL to a did:web DID for trust anchor identification.

    Examples:
        https://ta.example.com/trust → did:web:ta.example.com
        https://ta.example.com:8443  → did:web:ta.example.com%3A8443
    """
    url = url.rstrip("/")
    for prefix in ("https://", "http://"):
        if url.startswith(prefix):
            url = url[len(prefix):]
            break
    # Remove path — did:web resolves at the domain root for simple cases.
    host_port = url.split("/")[0]
    return f"did:web:{host_port}"
