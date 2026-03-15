"""EDC Catalog endpoint client.

Uses the EDC Management API's catalog federation endpoints to retrieve
the catalog of a remote connector and look up individual datasets.

Protocol note: EDC separates catalog negotiation (Management API) from DSP
catalog protocol messages (DSP adapter). This client only uses the Management
API side.
"""
from __future__ import annotations

from typing import Any

from .management_client import EdcManagementClient

_DSP_PROTOCOL = "dataspace-protocol-http"


class EdcCatalogClient:
    """Client for the EDC Catalog federation endpoints (POST /v2/catalog/request).

    Delegates all HTTP calls to ``EdcManagementClient``.
    """

    def __init__(self, management_client: EdcManagementClient) -> None:
        self._client = management_client

    async def request_catalog(
        self,
        counter_party_address: str,
        query_spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetch the full catalog from a remote connector's DSP endpoint.

        Args:
            counter_party_address: The DSP protocol endpoint of the provider
                connector (e.g. ``http://provider:8282/protocol``).
            query_spec: Optional EDC ``QuerySpec`` dict to filter datasets
                (e.g. ``{"filterExpression": [...]}``.

        Returns:
            Raw EDC catalog JSON-LD dict.
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
            "counterPartyAddress": counter_party_address,
            "protocol": _DSP_PROTOCOL,
        }
        if query_spec:
            body["querySpec"] = query_spec

        return await self._client.post("/v2/catalog/request", body)

    async def get_dataset(
        self,
        dataset_id: str,
        counter_party_address: str,
    ) -> dict[str, Any]:
        """Fetch a single dataset from a remote connector.

        Args:
            dataset_id: The ``@id`` of the target dataset / asset.
            counter_party_address: The DSP protocol endpoint of the provider.

        Returns:
            Raw EDC dataset JSON-LD dict.
        """
        body: dict[str, Any] = {
            "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
            "@id": dataset_id,
            "counterPartyAddress": counter_party_address,
            "protocol": _DSP_PROTOCOL,
        }
        return await self._client.post("/v2/catalog/datasets/request", body)
