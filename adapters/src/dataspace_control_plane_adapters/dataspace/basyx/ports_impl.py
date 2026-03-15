"""BaSyx port implementations.

Bridges the BaSyx adapter clients to the core port interfaces defined in
core/domains/twins/ports.py.

Implementations:
- BasYxAasRegistry    → AasRegistryPort
- BasYxEndpointProbe  → TwinEndpointProbePort
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from dataspace_control_plane_core.domains._shared.ids import TenantId
from dataspace_control_plane_core.domains.twins.model.value_objects import (
    EndpointHealth,
    TwinDescriptor,
)

from .aas_registry_client import AasRegistryClient
from .config import BasYxSettings
from .descriptor_mappers import (
    encode_aas_id,
    map_canonical_to_shell_descriptor,
)
from .errors import AasDescriptorNotFoundError

logger = logging.getLogger(__name__)


class BasYxAasRegistry:
    """Implements core/domains/twins/ports.py AasRegistryPort.

    Synchronises AAS Shell Descriptors with the BaSyx AAS Registry.

    The tenant_id is stored as a specificAssetId on the shell descriptor
    so that per-tenant isolation can be enforced at query time.
    """

    _TENANT_ASSET_ID_NAME = "tenantId"

    def __init__(self, cfg: BasYxSettings) -> None:
        self._cfg = cfg

    async def register_shell(
        self, tenant_id: TenantId, descriptor: TwinDescriptor
    ) -> None:
        """Register or update an AAS shell in the BaSyx registry.

        Maps the canonical TwinDescriptor to a BaSyx shell descriptor and
        POSTs (or PUTs if it already exists) to the AAS Registry.

        Args:
            tenant_id: Owning tenant identifier, embedded as a specificAssetId.
            descriptor: Canonical TwinDescriptor from core.
        """
        # Build canonical dict from TwinDescriptor value object fields.
        canonical_dict = _descriptor_to_canonical_dict(tenant_id, descriptor)
        shell = map_canonical_to_shell_descriptor(canonical_dict)

        aas_id = shell.get("id") or ""
        aas_id_b64 = encode_aas_id(aas_id)

        async with AasRegistryClient(self._cfg) as client:
            # Try to update first; if not found, create.
            try:
                existing = await client.get_shell_descriptor(aas_id_b64)
                # Descriptor exists — update it.
                await client.put_shell_descriptor(aas_id_b64, shell)
                logger.debug(
                    "Updated AAS shell descriptor id=%s tenant=%s", aas_id, tenant_id
                )
            except AasDescriptorNotFoundError:
                await client.post_shell_descriptor(shell)
                logger.debug(
                    "Registered new AAS shell descriptor id=%s tenant=%s",
                    aas_id,
                    tenant_id,
                )

    async def deregister_shell(self, tenant_id: TenantId, shell_id: str) -> None:
        """Remove an AAS shell from the BaSyx registry.

        Args:
            tenant_id: Owning tenant identifier (used for audit, not for filtering here).
            shell_id: Raw AAS ID of the shell to remove.
        """
        aas_id_b64 = encode_aas_id(shell_id)
        async with AasRegistryClient(self._cfg) as client:
            try:
                await client.delete_shell_descriptor(aas_id_b64)
                logger.debug(
                    "Deregistered AAS shell id=%s tenant=%s", shell_id, tenant_id
                )
            except AasDescriptorNotFoundError:
                # Idempotent — if not present, treat as success.
                logger.debug(
                    "AAS shell id=%s not found on deregister (already absent)", shell_id
                )


class BasYxEndpointProbe:
    """Implements core/domains/twins/ports.py TwinEndpointProbePort.

    Probes a twin endpoint URL with a short-timeout HTTP GET to determine
    reachability. No authentication is sent — probes are connectivity checks
    only.
    """

    def __init__(self, cfg: BasYxSettings) -> None:
        self._cfg = cfg

    async def probe(self, endpoint_url: str) -> EndpointHealth:
        """Probe a twin endpoint URL for reachability.

        Sends an unauthenticated GET with a short timeout (probe_timeout_s
        from config). Returns EndpointHealth regardless of HTTP status — only
        connection failures mark the endpoint as unreachable.

        Args:
            endpoint_url: The full URL of the twin/submodel endpoint to probe.

        Returns:
            EndpointHealth snapshot with is_reachable and last_checked_at.
        """
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._cfg.probe_timeout_s) as client:
                await client.get(endpoint_url)
            is_reachable = True
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
            is_reachable = False

        return EndpointHealth(
            endpoint_url=endpoint_url,
            is_reachable=is_reachable,
            last_checked_at=datetime.now(timezone.utc),
        )


def _descriptor_to_canonical_dict(
    tenant_id: TenantId, descriptor: TwinDescriptor
) -> dict:
    """Build a canonical dict from a TwinDescriptor value object.

    Extracts fields from the nested AasShellRef, SubmodelRef, and EndpointRef
    objects into the flat dict shape expected by map_canonical_to_shell_descriptor.
    """
    shell_ref = descriptor.shell_ref

    submodels: list[dict] = []
    for sm_ref in descriptor.submodels:
        sm_entry: dict = {
            "id": sm_ref.submodel_id,
        }
        semantic_id = getattr(sm_ref, "semantic_id", None)
        if semantic_id:
            sm_entry["semantic_id"] = str(semantic_id)
        submodels.append(sm_entry)

    # Add endpoint URLs from EndpointRef list.
    for ep_ref in descriptor.endpoints:
        # Match endpoints to submodels by interface type.
        for sm_entry in submodels:
            if not sm_entry.get("endpoint_url"):
                sm_entry["endpoint_url"] = ep_ref.endpoint_url
                sm_entry["interface"] = getattr(ep_ref, "interface", "SUBMODEL-3.0")
                break

    # Embed tenantId as a specificAssetId for multi-tenancy isolation.
    specific_asset_ids: list[dict] = [
        {
            "name": BasYxAasRegistry._TENANT_ASSET_ID_NAME,
            "value": str(tenant_id),
        }
    ]

    return {
        "twin_id": shell_ref.aas_id,
        "global_asset_id": shell_ref.global_asset_id,
        "specific_asset_ids": specific_asset_ids,
        "submodels": submodels,
        "endpoints": [],
    }
