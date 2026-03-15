"""Public import surface for the Gaia-X trust and compliance adapter."""
from __future__ import annotations

from .compliance_client import GaiaXComplianceClient
from .config import GaiaXSettings
from .credential_translation import (
    translate_compliance_credential,
    translate_participant_credential,
)
from .errors import (
    GaiaXComplianceError,
    GaiaXError,
    GaiaXSelfDescriptionError,
    GaiaXTrustError,
)
from .ports_impl import GaiaXTrustAnchorAdapterPort
from .self_description_client import GaiaXSelfDescriptionClient
from .trust_anchor_client import GaiaXTrustAnchorClient

__all__ = [
    "GaiaXSettings",
    "GaiaXSelfDescriptionClient",
    "GaiaXComplianceClient",
    "GaiaXTrustAnchorClient",
    "GaiaXTrustAnchorAdapterPort",
    "translate_participant_credential",
    "translate_compliance_credential",
    "GaiaXError",
    "GaiaXComplianceError",
    "GaiaXTrustError",
    "GaiaXSelfDescriptionError",
]
