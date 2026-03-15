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

from .config import DspSettings
from .errors import (
    DspError,
    DspNegotiationError,
    DspTransferError,
    DspValidationError,
)
from .health import DspHealthProbe
from .ports_impl import DspAgreementRegistry

__all__ = [
    # Configuration
    "DspSettings",
    # Port implementations
    "DspAgreementRegistry",
    "DspHealthProbe",
    # Errors
    "DspError",
    "DspValidationError",
    "DspNegotiationError",
    "DspTransferError",
]
