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
from .mappers import map_asset_to_ref, map_catalog_to_offer_snapshots, map_negotiation_state
from .negotiation_client import EdcNegotiationClient
from .ports_impl import EdcAgreementRegistry, EdcCatalogLookup, EdcConnectorProvisioning
from .raw_models import (
    EdcAssetRaw,
    EdcCatalogRaw,
    EdcContractAgreementRaw,
    EdcContractOfferRaw,
    EdcNegotiationRaw,
    EdcTransferProcessRaw,
)
from .request_decoration import TransferDecoration
from .transfer_client import EdcTransferClient
from .webhook_mappers import (
    extract_agreement_id,
    map_negotiation_event,
    map_transfer_event,
)

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
    "EdcConnectorProvisioning",
    # Health
    "EdcHealthProbe",
    # Wire models
    "EdcAssetRaw",
    "EdcCatalogRaw",
    "EdcContractAgreementRaw",
    "EdcContractOfferRaw",
    "EdcNegotiationRaw",
    "EdcTransferProcessRaw",
    # Mappers
    "map_asset_to_ref",
    "map_catalog_to_offer_snapshots",
    "map_negotiation_state",
    # Webhook mappers
    "map_negotiation_event",
    "map_transfer_event",
    "extract_agreement_id",
    # Data-plane decoration
    "TransferDecoration",
    # Errors
    "EdcError",
    "EdcNegotiationError",
    "EdcTransferError",
    "EdcAssetNotFoundError",
    "EdcPolicyNotFoundError",
    "EdcWebhookParseError",
]
