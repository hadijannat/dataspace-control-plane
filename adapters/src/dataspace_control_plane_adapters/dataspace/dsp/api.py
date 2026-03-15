"""Public import surface for the DSP adapter.

All consumers (apps/control-api, apps/temporal-workers, tests/) must import
from this module only. Never import from internal DSP sub-modules directly.

Typical usage::

    from dataspace_control_plane_adapters.dataspace.dsp.api import (
        DspSettings,
        DspCatalogRequest,
        validate_catalog_request,
        map_catalog_to_offers,
        DspAgreementRegistry,
    )

    settings = DspSettings()
    registry = DspAgreementRegistry(settings)
"""
from __future__ import annotations

from .canonical_mapper import (
    map_agreement_to_record,
    map_catalog_to_offers,
    map_negotiation_event,
    map_transfer_request,
)
from .config import DspSettings
from .errors import (
    DspError,
    DspNegotiationError,
    DspTransferError,
    DspValidationError,
)
from .messages import (
    DspCatalogRequest,
    DspCatalogResponse,
    DspContractAgreementMessage,
    DspContractOfferMessage,
    DspContractRequestMessage,
    DspNegotiationEventMessage,
    DspTransferRequestMessage,
    DspTransferStartMessage,
)
from .ports_impl import DspAgreementRegistry
from .raw_models import (
    DspCatalogRequest,
    DspCatalogResponse,
    DspContractAgreementMessage,
    DspContractOfferMessage,
    DspContractRequestMessage,
    DspNegotiationEventMessage,
    DspTransferRequestMessage,
    DspTransferStartMessage,
)
from .validators import (
    validate_agreement_message,
    validate_catalog_request,
    validate_contract_offer,
    validate_contract_request,
    validate_negotiation_event,
    validate_transfer_request,
)

__all__ = [
    # Configuration
    "DspSettings",
    # Message models (also used as raw_models)
    "DspCatalogRequest",
    "DspCatalogResponse",
    "DspContractRequestMessage",
    "DspContractOfferMessage",
    "DspContractAgreementMessage",
    "DspNegotiationEventMessage",
    "DspTransferRequestMessage",
    "DspTransferStartMessage",
    # Validators
    "validate_catalog_request",
    "validate_contract_request",
    "validate_contract_offer",
    "validate_agreement_message",
    "validate_negotiation_event",
    "validate_transfer_request",
    # Canonical mappers
    "map_catalog_to_offers",
    "map_agreement_to_record",
    "map_transfer_request",
    "map_negotiation_event",
    # Port implementations
    "DspAgreementRegistry",
    # Errors
    "DspError",
    "DspValidationError",
    "DspNegotiationError",
    "DspTransferError",
]
