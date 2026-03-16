"""DSP adapter implementation of core/ ports.

Implements:
- ``AgreementRegistryPort`` from core/domains/contracts/ports.py

The DSP adapter's role in agreement registration is to publish the protocol-level
acknowledgement (ACK) back to the provider via the DSP callback endpoint. It does
not manage connector lifecycle or EDC-specific resources — that is the EDC adapter's
responsibility.

Rules (adapters/CLAUDE.md):
- No business logic — adapters move and normalize data only.
- Secrets never appear in return values or logs.
- All external errors are translated before propagating upward.
"""
from __future__ import annotations

import logging
from typing import Any

from ..._shared.auth import StaticTokenProvider
from ..._shared.http import AsyncAdapterClient
from .config import DspSettings
from .errors import DspNegotiationError
from .messages import _DSP_CONTEXT

logger = logging.getLogger(__name__)


class DspAgreementRegistry:
    """implements core/domains/contracts/ports.py :: AgreementRegistryPort

    Sends a DSP ContractAgreementVerificationMessage ACK to the provider's
    callback endpoint to signal that the consumer has verified and accepted
    the concluded contract agreement.

    This is the protocol-side complement to ``EdcAgreementRegistry`` which
    handles the EDC management-plane side. Both may be composed at the
    application layer.
    """

    def __init__(
        self,
        settings: DspSettings,
        token_provider: StaticTokenProvider | None = None,
    ) -> None:
        self._settings = settings
        self._token_provider = token_provider

    async def register_agreement(
        self,
        tenant_id: Any,
        agreement_id: str,
        policy_snapshot_id: str,
    ) -> None:
        """Acknowledge a concluded DSP agreement by posting a verification ACK.

        In DSP 2025-1 the consumer acknowledges the provider's
        ``ContractAgreementMessage`` by sending a
        ``ContractAgreementVerificationMessage`` back to the provider's
        callback URL.

        Args:
            tenant_id: Opaque tenant identifier (used for logging only).
            agreement_id: The ``@id`` of the concluded ODRL agreement.
            policy_snapshot_id: The policy snapshot ID; embedded as a private
                annotation in the verification message for auditability.

        Raises:
            DspNegotiationError: If the ACK delivery fails.
        """
        callback_url = str(self._settings.callback_base_url)
        # Derive the provider's verification endpoint from the agreement ID.
        # DSP spec: POST <provider-base>/negotiations/<consumerPid>/agreement/verification
        # Here we use the agreement_id as a stable routing key.
        verification_endpoint = (
            f"{callback_url.rstrip('/')}/negotiations/{agreement_id}/agreement/verification"
        )

        ack_body: dict[str, Any] = {
            "@context": _DSP_CONTEXT,
            "@type": "dspace:ContractAgreementVerificationMessage",
            "dspace:providerPid": agreement_id,
            "dspace:consumerPid": agreement_id,
            # Private annotation — not part of DSP spec, stripped by the provider.
            "_policySnapshotId": policy_snapshot_id,
        }

        http = AsyncAdapterClient(
            base_url=verification_endpoint,
            token_provider=self._token_provider,
            timeout=self._settings.request_timeout_s,
        )

        try:
            async with http as client:
                await client.post("", json=ack_body)
        except Exception as exc:
            logger.error(
                "DSP agreement ACK failed for agreement=%s tenant=%s: %s",
                agreement_id,
                tenant_id,
                exc,
                exc_info=True,
            )
            raise DspNegotiationError(
                f"Failed to acknowledge DSP agreement {agreement_id}: {exc}"
            ) from exc

        logger.info(
            "DSP agreement ACK sent for agreement=%s policy_snapshot=%s tenant=%s",
            agreement_id,
            policy_snapshot_id,
            tenant_id,
        )
