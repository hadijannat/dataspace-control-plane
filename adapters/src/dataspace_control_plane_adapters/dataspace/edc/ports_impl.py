"""EDC adapter implementations of core/ ports.

Implements:
- ``AgreementRegistryPort``   from core/domains/contracts/ports.py
- ``CatalogLookupPort``       from core/domains/contracts/ports.py
- ``ConnectorProvisioningPort`` from core/domains/onboarding/ports.py

Rules (adapters/CLAUDE.md):
- No business logic — adapters move and normalize data only.
- Secrets never appear in return values or logs.
- All external errors are translated before propagating upward.
"""
from __future__ import annotations

import ipaddress
import urllib.parse
from datetime import datetime, timezone
import logging
from typing import Any

import httpx

from dataspace_control_plane_core.domains.contracts.model.value_objects import (
    OfferSnapshot,
    TransferAuthorization,
)
from dataspace_control_plane_core.domains.twins.model.value_objects import (
    EndpointHealth,
)

from ..._shared.errors import AdapterNotFoundError
from .asset_client import EdcAssetClient
from .errors import EdcAssetNotFoundError, EdcNegotiationError, EdcPolicyNotFoundError
from .management_client import EdcManagementClient
from .negotiation_client import EdcNegotiationClient
from .mappers import map_asset_to_ref
from .raw_models import EdcAssetRaw, EdcPolicyDefinitionRaw

logger = logging.getLogger(__name__)


class EdcAgreementRegistry:
    """implements core/domains/contracts/ports.py :: AgreementRegistryPort

    Stores a concluded agreement reference against EDC by creating a minimal
    asset record in the provider's catalog extension endpoint. In deployments
    where the EDC catalog extension is not available, this writes a private
    property to a tracking asset so the agreement is traceable via the
    Management API.
    """

    def __init__(self, asset_client: EdcAssetClient) -> None:
        self._assets = asset_client

    async def register_agreement(
        self,
        tenant_id: Any,
        agreement_id: str,
        policy_snapshot_id: str,
    ) -> None:
        """Register a concluded agreement in EDC.

        Creates a lightweight tracking asset whose properties record the
        ``agreement_id`` and ``policy_snapshot_id``. This asset is marked
        private so it does not appear in catalog offers.

        Args:
            tenant_id: Opaque tenant identifier (passed through, not stored in EDC).
            agreement_id: The concluded contract agreement ID from the DSP flow.
            policy_snapshot_id: The policy snapshot that governed this agreement.
        """
        tracking_asset_id = f"agreement-tracking:{agreement_id}"
        properties: dict[str, Any] = {
            "name": f"Agreement tracking — {agreement_id}",
            "agreement_id": agreement_id,
            "policy_snapshot_id": policy_snapshot_id,
            "tenant_id": str(tenant_id),
            "tracking": "true",
        }
        # DataAddress is required by EDC even for tracking assets.
        data_address: dict[str, Any] = {
            "@type": "DataAddress",
            "type": "NoOp",
        }
        try:
            await self._assets.create_asset(
                asset_id=tracking_asset_id,
                properties=properties,
                data_address=data_address,
                private_properties={"visible_in_catalog": "false"},
            )
        except Exception as exc:
            logger.error(
                "Failed to register agreement %s in EDC: %s",
                agreement_id,
                exc,
                exc_info=True,
            )
            raise EdcNegotiationError(
                f"Could not register agreement {agreement_id} in EDC: {exc}"
            ) from exc

        logger.info(
            "Registered agreement %s (policy snapshot %s) for tenant %s in EDC",
            agreement_id,
            policy_snapshot_id,
            tenant_id,
        )


class EdcCatalogLookup:
    """implements core/domains/contracts/ports.py :: CatalogLookupPort

    Looks up asset metadata and policy IDs via the EDC Management API.
    Returns canonical dicts; never domain aggregates.
    """

    def __init__(self, management_client: EdcManagementClient) -> None:
        self._client = management_client

    async def get_asset_ref(self, tenant_id: Any, asset_id: str) -> dict[str, Any]:
        """Fetch a canonical asset-reference dict from EDC.

        Args:
            tenant_id: Opaque tenant identifier (used for logging only).
            asset_id: The EDC asset ``@id``.

        Returns:
            Canonical dict with keys ``asset_id``, ``properties``, ``data_address``.

        Raises:
            EdcAssetNotFoundError: If the asset does not exist in EDC.
        """
        try:
            raw_dict = await self._client.get(f"/v2/assets/{asset_id}")
        except AdapterNotFoundError as exc:
            raise EdcAssetNotFoundError(
                f"Asset '{asset_id}' not found in EDC for tenant {tenant_id}",
                upstream_code=exc.upstream_code,
            ) from exc

        # Validate wire shape before mapping.
        raw = EdcAssetRaw.model_validate(raw_dict)
        return map_asset_to_ref(raw)

    async def get_offer_policy_id(self, tenant_id: Any, offer_id: str) -> str:
        """Fetch the policy ID for a given EDC policy definition / offer ID.

        Args:
            tenant_id: Opaque tenant identifier (used for logging only).
            offer_id: The EDC policy definition ``@id`` that corresponds to the offer.

        Returns:
            The ``@id`` string of the policy definition.

        Raises:
            EdcPolicyNotFoundError: If no policy definition with ``offer_id`` exists.
        """
        try:
            raw_dict = await self._client.get(f"/v2/policydefinitions/{offer_id}")
        except AdapterNotFoundError as exc:
            raise EdcPolicyNotFoundError(
                f"Policy definition '{offer_id}' not found in EDC for tenant {tenant_id}",
                upstream_code=exc.upstream_code,
            ) from exc

        policy_raw = EdcPolicyDefinitionRaw.model_validate(raw_dict)
        return policy_raw.id


class EdcConnectorProvisioning:
    """implements core/domains/onboarding/ports.py :: ConnectorProvisioningPort

    Bootstraps a new EDC connector instance by registering it with the
    Management API. In practice this means creating the initial tenant-specific
    tracking assets and verifying the connector's Management API is reachable.
    """

    def __init__(self, management_client: EdcManagementClient) -> None:
        self._client = management_client

    async def bootstrap_connector(
        self,
        tenant_id: Any,
        legal_entity_id: Any,
        connector_url: str,
    ) -> None:
        """Bootstrap and verify an EDC connector for a legal entity.

        Steps:
        1. Probe the connector's Management API health endpoint.
        2. Register a sentinel tracking asset so we can verify API-key auth.

        Args:
            tenant_id: Opaque tenant identifier.
            legal_entity_id: Legal entity this connector belongs to.
            connector_url: Base URL of the connector's Management API.

        Raises:
            AdapterUnavailableError: If the connector Management API is unreachable.
            AdapterAuthError: If the API key is rejected.
            EdcNegotiationError: If registration fails for an unexpected reason.
        """
        # Step 1: verify reachability via a lightweight GET.
        try:
            await self._client.get("/v2/assets?limit=1")
        except Exception as exc:
            logger.error(
                "EDC connector bootstrap failed — management API unreachable at %s: %s",
                connector_url,
                exc,
            )
            raise

        # Step 2: write a sentinel tracking asset to confirm write access.
        sentinel_id = f"bootstrap-sentinel:{tenant_id}:{legal_entity_id}"
        sentinel_properties: dict[str, Any] = {
            "name": "Bootstrap sentinel",
            "tenant_id": str(tenant_id),
            "legal_entity_id": str(legal_entity_id),
            "connector_url": connector_url,
            "bootstrap_sentinel": "true",
        }
        sentinel_data_address: dict[str, Any] = {
            "@type": "DataAddress",
            "type": "NoOp",
        }

        try:
            from .asset_client import EdcAssetClient

            asset_client = EdcAssetClient(self._client)
            await asset_client.create_asset(
                asset_id=sentinel_id,
                properties=sentinel_properties,
                data_address=sentinel_data_address,
            )
        except Exception as exc:
            logger.error(
                "EDC connector bootstrap sentinel creation failed for %s/%s: %s",
                tenant_id,
                legal_entity_id,
                exc,
            )
            raise

        logger.info(
            "EDC connector bootstrapped for tenant=%s legal_entity=%s url=%s",
            tenant_id,
            legal_entity_id,
            connector_url,
        )


class EdcNegotiationPort:
    """Implements ``NegotiationPort`` by submitting a follow-up EDC request.

    EDC's management API expects a complete offer payload when the consumer
    responds. The adapter resolves the referenced policy definition locally and
    creates a new request against the counterparty's DSP endpoint.
    """

    def __init__(self, management_client: EdcManagementClient) -> None:
        self._client = management_client
        self._negotiations = EdcNegotiationClient(management_client)

    async def submit_counter_offer(
        self,
        tenant_id: Any,
        negotiation_id: Any,
        offer: OfferSnapshot,
    ) -> None:
        counter_party_address = offer.provider.connector_url
        if not counter_party_address:
            raise EdcNegotiationError(
                "Cannot submit EDC counter-offer without provider.connector_url"
            )

        try:
            raw_policy = await self._client.get(f"/v2/policydefinitions/{offer.policy_id}")
            policy = EdcPolicyDefinitionRaw.model_validate(raw_policy)
            await self._negotiations.initiate(
                counter_party_address=counter_party_address,
                offer={
                    "offerId": offer.offer_id,
                    "assetId": offer.asset.asset_id,
                    "policy": policy.policy,
                },
                connector_id=offer.asset.connector_id or None,
            )
        except Exception as exc:
            logger.error(
                "Failed to submit EDC counter-offer negotiation=%s tenant=%s offer=%s: %s",
                negotiation_id,
                tenant_id,
                offer.offer_id,
                exc,
            )
            raise EdcNegotiationError(
                f"Could not submit EDC counter-offer {offer.offer_id}: {exc}"
            ) from exc


class EdcTransferObservation:
    """Implements ``TransferObservationPort`` with EDC-local tracking assets."""

    def __init__(self, asset_client: EdcAssetClient) -> None:
        self._assets = asset_client

    async def record_transfer_authorization(
        self,
        tenant_id: Any,
        authorization: TransferAuthorization,
    ) -> None:
        tracking_asset_id = f"transfer-authorization:{authorization.authorization_id}"
        properties: dict[str, Any] = {
            "name": f"Transfer authorization {authorization.authorization_id}",
            "authorization_id": authorization.authorization_id,
            "agreement_id": authorization.agreement_id,
            "asset_id": authorization.asset_id,
            "tenant_id": str(tenant_id),
            "granted_at": authorization.granted_at.isoformat(),
        }
        if authorization.valid_until is not None:
            properties["valid_until"] = authorization.valid_until.isoformat()
        if authorization.is_revoked:
            properties["revoked"] = "true"

        try:
            await self._assets.create_asset(
                asset_id=tracking_asset_id,
                properties=properties,
                data_address={"@type": "DataAddress", "type": "NoOp"},
                private_properties={"visible_in_catalog": "false"},
            )
        except Exception as exc:
            logger.error(
                "Failed to record transfer authorization %s for tenant=%s: %s",
                authorization.authorization_id,
                tenant_id,
                exc,
            )
            raise EdcNegotiationError(
                f"Could not record transfer authorization {authorization.authorization_id}: {exc}"
            ) from exc


_SSRF_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / AWS metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _validate_probe_url(url: str) -> None:
    """Reject URLs that would allow Server-Side Request Forgery.

    Blocks private/reserved IP ranges and non-http(s) schemes.  DNS-level
    SSRF mitigation (post-resolution IP check) is the responsibility of the
    network egress layer in infra/.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Probe URL scheme must be http or https, got {parsed.scheme!r}: {url!r}"
        )
    hostname = (parsed.hostname or "").lower()
    if not hostname or hostname == "localhost":
        raise ValueError(f"Probe URL hostname not allowed: {hostname!r}")
    try:
        addr = ipaddress.ip_address(hostname)
        for net in _SSRF_BLOCKED_NETWORKS:
            if addr in net:
                raise ValueError(
                    f"Probe URL targets private/reserved address {hostname!r}"
                )
    except ValueError as exc:
        if "Probe URL" in str(exc):
            raise
        # hostname is a domain name, not an IP literal — allow through.


class EdcConnectorAssetProbe:
    """Implements ``ConnectorAssetPort`` using a lightweight endpoint probe."""

    def __init__(self, timeout_s: float = 5.0) -> None:
        self._timeout_s = timeout_s

    async def probe(self, endpoint_url: str) -> EndpointHealth:
        _validate_probe_url(endpoint_url)  # raises ValueError on SSRF-risky URLs
        is_reachable = False
        try:
            async with httpx.AsyncClient(timeout=self._timeout_s) as client:
                resp = await client.get(endpoint_url)
            # Treat any HTTP response (including 4xx auth errors) as reachable —
            # a 401/403 means the endpoint is up but requires credentials, which
            # is the expected state for a protected connector surface.
            is_reachable = True
            if not resp.is_success:
                logger.debug(
                    "Probe %s returned HTTP %d (still reachable)",
                    endpoint_url,
                    resp.status_code,
                )
        except Exception as exc:
            logger.warning("Probe %s failed: %s: %s", endpoint_url, type(exc).__name__, exc)

        return EndpointHealth(
            endpoint_url=endpoint_url,
            is_reachable=is_reachable,
            last_checked_at=datetime.now(timezone.utc),
        )
