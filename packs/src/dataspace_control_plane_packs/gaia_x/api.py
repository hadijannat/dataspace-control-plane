"""Public import surface for the Gaia-X Trust Framework pack."""
from __future__ import annotations

import pathlib
from typing import Any

from .._shared.capabilities import PackCapability
from .._shared.manifest import PackManifest
from .baseline.compliance_rules import GaiaXComplianceValidator
from .baseline.credentials import GaiaXCredentialProfileProvider
from .baseline.policies import GaiaXPolicyDialectProvider
from .baseline.self_descriptions import SelfDescriptionSchema, validate_self_description
from .baseline.trust_anchors import GaiaXBaselineTrustAnchorOverlay, TrustAnchor, TrustAnchorConfig
from .baseline.trust_framework import GX_TRUST_FRAMEWORK_URI, GX_TRUST_FRAMEWORK_VERSION
from .data_exchange_profiles import GaiaXDataExchangeProfileProvider
from .evidence import GaiaXEvidenceAugmenter
from .requirements import GaiaXRequirementProvider

_MANIFEST_PATH = pathlib.Path(__file__).parent / "manifest.toml"
MANIFEST: PackManifest = PackManifest.from_toml(_MANIFEST_PATH)

PROVIDERS: dict[PackCapability, Any] = {
    PackCapability.REQUIREMENT_PROVIDER: GaiaXRequirementProvider(),
    PackCapability.CREDENTIAL_PROFILE: GaiaXCredentialProfileProvider(),
    PackCapability.TRUST_ANCHOR_OVERLAY: GaiaXBaselineTrustAnchorOverlay(),
    PackCapability.POLICY_DIALECT: GaiaXPolicyDialectProvider(),
    PackCapability.DATA_EXCHANGE_PROFILE: GaiaXDataExchangeProfileProvider(),
    PackCapability.EVIDENCE_AUGMENTER: GaiaXEvidenceAugmenter(),
}

__all__ = [
    "MANIFEST",
    "PROVIDERS",
    "GaiaXRequirementProvider",
    "GaiaXCredentialProfileProvider",
    "GaiaXBaselineTrustAnchorOverlay",
    "GaiaXPolicyDialectProvider",
    "GaiaXDataExchangeProfileProvider",
    "GaiaXEvidenceAugmenter",
    "GaiaXComplianceValidator",
    "SelfDescriptionSchema",
    "validate_self_description",
    "TrustAnchor",
    "TrustAnchorConfig",
    "GX_TRUST_FRAMEWORK_VERSION",
    "GX_TRUST_FRAMEWORK_URI",
]
