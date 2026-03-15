"""EDC Contract Negotiation Management API client.

Covers the full negotiation lifecycle: initiate → poll → get agreement → terminate.

EDC state machine (simplified):
  INITIAL → REQUESTING → REQUESTED → OFFERING → OFFERED → ACCEPTING → ACCEPTED
  → AGREEING → AGREED → VERIFYING → VERIFIED → FINALIZING → FINALIZED
  or any state → TERMINATING → TERMINATED

This client does not interpret state; see mappers.py for state mapping.
"""
from __future__ import annotations

from typing import Any

from .management_client import EdcManagementClient

_DSP_PROTOCOL = "dataspace-protocol-http"


class EdcNegotiationClient:
    """Client for EDC contract negotiation endpoints (``/v2/contractnegotiations``)."""

    def __init__(self, management_client: EdcManagementClient) -> None:
        self._client = management_client

    async def initiate(
        self,
        counter_party_address: str,
        offer: dict[str, Any],
        connector_id: str | None = None,
    ) -> str:
        """Initiate a contract negotiation with a remote provider.

        Args:
            counter_party_address: DSP protocol endpoint of the provider connector.
            offer: ODRL ``Offer`` dict (must include ``offerId``, ``assetId``,
                ``policy``).
            connector_id: Optional EDC connector identifier for the provider.

        Returns:
            The negotiation ID (``@id``) of the newly created negotiation.
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
            "@type": "ContractRequest",
            "counterPartyAddress": counter_party_address,
            "protocol": _DSP_PROTOCOL,
            "offer": offer,
        }
        if connector_id:
            body["connectorId"] = connector_id

        result = await self._client.post("/v2/contractnegotiations", body)
        return result["@id"]

    async def get(self, negotiation_id: str) -> dict[str, Any]:
        """Fetch the current state of a contract negotiation.

        Args:
            negotiation_id: The negotiation ``@id`` returned by :meth:`initiate`.

        Returns:
            Raw EDC negotiation JSON-LD dict.
        """
        return await self._client.get(f"/v2/contractnegotiations/{negotiation_id}")

    async def get_agreement(self, negotiation_id: str) -> dict[str, Any]:
        """Fetch the contract agreement associated with a finalized negotiation.

        Args:
            negotiation_id: A negotiation in FINALIZED state.

        Returns:
            Raw EDC contract agreement JSON-LD dict.
        """
        return await self._client.get(
            f"/v2/contractnegotiations/{negotiation_id}/agreement"
        )

    async def terminate(self, negotiation_id: str, reason: str) -> None:
        """Terminate an in-progress negotiation.

        Args:
            negotiation_id: The negotiation to terminate.
            reason: Human-readable termination reason (sent to the provider).
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
            "@type": "TerminationMessage",
            "reason": reason,
        }
        await self._client.post(
            f"/v2/contractnegotiations/{negotiation_id}/terminate", body
        )
