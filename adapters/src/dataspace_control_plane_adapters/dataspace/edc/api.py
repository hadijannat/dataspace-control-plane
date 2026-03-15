"""Public import surface for the EDC adapter.

All consumers (apps/control-api, apps/temporal-workers, tests/) must import
from this module only. Never import from internal EDC sub-modules directly.

Typical wiring at container startup::

    from dataspace_control_plane_adapters.dataspace.edc.api import (
        EdcSettings,
        EdcManagementClient,
        EdcCatalogClient,
        EdcNegotiationClient,
        EdcTransferClient,
        EdcAssetClient,
        EdcAgreementRegistry,
        EdcCatalogLookup,
        EdcConnectorProvisioning,
        EdcHealthProbe,
    )

    settings = EdcSettings()
    async with EdcManagementClient(settings) as mgmt:
        catalog = EdcCatalogClient(mgmt)
        ...
"""
from __future__ import annotations

from .asset_client import EdcAssetClient
from .catalog_client import EdcCatalogClient
from .config import EdcSettings
from .errors import (
    EdcAssetNotFoundError,
    EdcError,
    EdcNegotiationError,
    EdcPolicyNotFoundError,
    EdcTransferError,
    EdcWebhookParseError,
)
from .health import EdcHealthProbe
from .management_client import EdcManagementClient
from .negotiation_client import EdcNegotiationClient
from .ports_impl import (
    EdcAgreementRegistry,
    EdcCatalogLookup,
    EdcConnectorAssetProbe,
    EdcConnectorProvisioning,
    EdcNegotiationPort,
    EdcTransferObservation,
)
from .transfer_client import EdcTransferClient

__all__ = [
    # Configuration
    "EdcSettings",
    # Core clients
    "EdcManagementClient",
    "EdcCatalogClient",
    "EdcNegotiationClient",
    "EdcTransferClient",
    "EdcAssetClient",
    # Port implementations
    "EdcAgreementRegistry",
    "EdcCatalogLookup",
    "EdcNegotiationPort",
    "EdcTransferObservation",
    "EdcConnectorAssetProbe",
    "EdcConnectorProvisioning",
    # Health
    "EdcHealthProbe",
    # Errors
    "EdcError",
    "EdcNegotiationError",
    "EdcTransferError",
    "EdcAssetNotFoundError",
    "EdcPolicyNotFoundError",
    "EdcWebhookParseError",
]
