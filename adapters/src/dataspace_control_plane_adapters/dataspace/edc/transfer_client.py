"""EDC Transfer Process Management API client.

Covers the full transfer lifecycle: initiate → get → suspend → resume → deprovision.

EDC transfer state machine (simplified):
  INITIAL → PROVISIONING → PROVISIONED → REQUESTING → REQUESTED → STARTING
  → STARTED → COMPLETING → COMPLETED
  or → SUSPENDING → SUSPENDED → RESUMING → (back to STARTED)
  or → TERMINATING → TERMINATED
  or → DEPROVISIONING → DEPROVISIONED
"""
from __future__ import annotations

from typing import Any

from .management_client import EdcManagementClient

_DSP_PROTOCOL = "dataspace-protocol-http"


class EdcTransferClient:
    """Client for EDC transfer process endpoints (``/v2/transferprocesses``)."""

    def __init__(self, management_client: EdcManagementClient) -> None:
        self._client = management_client

    async def initiate(
        self,
        contract_agreement_id: str,
        asset_id: str,
        counter_party_address: str,
        data_destination: dict[str, Any],
        transfer_type: str = "HttpData-PULL",
        connector_id: str | None = None,
        private_properties: dict[str, Any] | None = None,
    ) -> str:
        """Initiate a data transfer process.

        Args:
            contract_agreement_id: The ``@id`` of the agreed contract.
            asset_id: The ``@id`` of the asset to transfer.
            counter_party_address: DSP protocol endpoint of the provider connector.
            data_destination: EDC ``DataAddress`` dict describing where data
                should land (e.g. ``{"@type": "HttpProxy"}`` for consumer pull).
            transfer_type: EDC transfer type string (default ``"HttpData-PULL"``).
            connector_id: Optional provider connector identifier.
            private_properties: Optional private properties forwarded to the
                data-plane but not visible to the provider.

        Returns:
            The transfer process ID (``@id``).
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
            "@type": "TransferRequest",
            "contractId": contract_agreement_id,
            "assetId": asset_id,
            "counterPartyAddress": counter_party_address,
            "protocol": _DSP_PROTOCOL,
            "dataDestination": data_destination,
            "transferType": transfer_type,
        }
        if connector_id:
            body["connectorId"] = connector_id
        if private_properties:
            body["privateProperties"] = private_properties

        result = await self._client.post("/v2/transferprocesses", body)
        return result["@id"]

    async def get(self, transfer_id: str) -> dict[str, Any]:
        """Fetch the current state of a transfer process.

        Args:
            transfer_id: The transfer process ``@id``.

        Returns:
            Raw EDC transfer process JSON-LD dict.
        """
        return await self._client.get(f"/v2/transferprocesses/{transfer_id}")

    async def deprovision(self, transfer_id: str) -> None:
        """Request deprovisioning of a completed or terminated transfer.

        Args:
            transfer_id: The transfer process ``@id``.
        """
        await self._client.post(
            f"/v2/transferprocesses/{transfer_id}/deprovision", {}
        )

    async def suspend(self, transfer_id: str, reason: str = "") -> None:
        """Suspend an active transfer process.

        Args:
            transfer_id: The transfer process ``@id``.
            reason: Optional human-readable reason for suspension.
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
            "@type": "SuspendTransfer",
        }
        if reason:
            body["reason"] = reason
        await self._client.post(
            f"/v2/transferprocesses/{transfer_id}/suspend", body
        )

    async def resume(self, transfer_id: str) -> None:
        """Resume a suspended transfer process.

        Args:
            transfer_id: The transfer process ``@id``.
        """
        await self._client.post(
            f"/v2/transferprocesses/{transfer_id}/resume", {}
        )
