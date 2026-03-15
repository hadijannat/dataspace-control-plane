"""EDC Asset, PolicyDefinition, and ContractDefinition management client.

Covers the provider-side data offering lifecycle:
  create asset → create policy → create contract definition → advertise in catalog

EDC SPI separation:
- Assets (``/v2/assets``) — data + metadata + DataAddress.
- Policy definitions (``/v2/policydefinitions``) — ODRL policy templates.
- Contract definitions (``/v2/contractdefinitions``) — link access policy,
  contract policy, and asset selector to form an offer.
"""
from __future__ import annotations

import uuid
from typing import Any

from .management_client import EdcManagementClient

_NS = "https://w3id.org/edc/v0.0.1/ns/"


class EdcAssetClient:
    """Client for EDC provider-side data offering management endpoints."""

    def __init__(self, management_client: EdcManagementClient) -> None:
        self._client = management_client

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    async def create_asset(
        self,
        asset_id: str,
        properties: dict[str, Any],
        data_address: dict[str, Any],
        private_properties: dict[str, Any] | None = None,
    ) -> str:
        """Create a new asset in EDC.

        Args:
            asset_id: Stable identifier for the asset (used as ``@id``).
            properties: Public metadata dict (e.g. name, description, content type).
            data_address: EDC ``DataAddress`` dict pointing to the physical data.
            private_properties: Optional private metadata not exposed in the catalog.

        Returns:
            The ``@id`` of the created asset (echoes ``asset_id``).
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": _NS},
            "@id": asset_id,
            "properties": properties,
            "dataAddress": data_address,
        }
        if private_properties:
            body["privateProperties"] = private_properties

        result = await self._client.post("/v2/assets", body)
        return result.get("@id", asset_id)

    async def get_asset(self, asset_id: str) -> dict[str, Any]:
        """Fetch a single asset by ID.

        Args:
            asset_id: The asset ``@id``.

        Returns:
            Raw EDC asset JSON-LD dict.

        Raises:
            AdapterNotFoundError: If no asset with ``asset_id`` exists.
        """
        return await self._client.get(f"/v2/assets/{asset_id}")

    async def delete_asset(self, asset_id: str) -> None:
        """Delete an asset.

        Args:
            asset_id: The asset ``@id`` to delete.
        """
        await self._client.delete(f"/v2/assets/{asset_id}")

    # ------------------------------------------------------------------
    # Policy definitions
    # ------------------------------------------------------------------

    async def create_policy_definition(
        self,
        policy_id: str,
        policy: dict[str, Any],
    ) -> str:
        """Create a policy definition in EDC.

        Args:
            policy_id: Stable identifier for the policy definition.
            policy: ODRL ``Policy`` dict (must include ``@type`` and permissions).

        Returns:
            The ``@id`` of the created policy definition.
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": _NS},
            "@id": policy_id,
            "policy": policy,
        }
        result = await self._client.post("/v2/policydefinitions", body)
        return result.get("@id", policy_id)

    async def get_policy_definition(self, policy_id: str) -> dict[str, Any]:
        """Fetch a policy definition by ID.

        Args:
            policy_id: The policy definition ``@id``.

        Returns:
            Raw EDC policy definition JSON-LD dict.

        Raises:
            AdapterNotFoundError: If no policy with ``policy_id`` exists.
        """
        return await self._client.get(f"/v2/policydefinitions/{policy_id}")

    async def delete_policy_definition(self, policy_id: str) -> None:
        """Delete a policy definition.

        Args:
            policy_id: The policy definition ``@id`` to delete.
        """
        await self._client.delete(f"/v2/policydefinitions/{policy_id}")

    # ------------------------------------------------------------------
    # Contract definitions
    # ------------------------------------------------------------------

    async def create_contract_definition(
        self,
        access_policy_id: str,
        contract_policy_id: str,
        asset_selector: list[dict[str, Any]],
        definition_id: str | None = None,
    ) -> str:
        """Create a contract definition linking policies and assets.

        The contract definition becomes visible in the provider's catalog and
        forms the basis of contract offers presented to consumers.

        Args:
            access_policy_id: ``@id`` of the policy that controls catalog access.
            contract_policy_id: ``@id`` of the policy embedded in the contract offer.
            asset_selector: List of EDC ``Criterion`` dicts filtering which assets
                this definition applies to (e.g.
                ``[{"operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                   "operator": "=", "operandRight": "<asset_id>"}]``).
            definition_id: Optional stable ID; a UUID is generated if omitted.

        Returns:
            The ``@id`` of the created contract definition.
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": _NS},
            "@id": definition_id or str(uuid.uuid4()),
            "accessPolicyId": access_policy_id,
            "contractPolicyId": contract_policy_id,
            "assetsSelector": asset_selector,
        }
        result = await self._client.post("/v2/contractdefinitions", body)
        return result.get("@id", body["@id"])
