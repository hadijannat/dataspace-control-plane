"""Public surface for the Catena-X ecosystem pack.

Import from this module to access the pack manifest, capability provider
instances, and all public classes. This is the only module callers outside
this package should import from.

cx-policy:* vocabulary is confined to this package and must not leak into
core/ or other layers.
"""
from __future__ import annotations

import pathlib
import tomllib
from typing import Any

from .._shared.manifest import PackManifest
from .._shared.capabilities import PackCapability

from .credential_profiles import CatenaxCredentialProfileProvider
from .evidence import CatenaxEvidenceAugmenter
from .identifiers import (
    BpnaSchemeProvider,
    BpnlSchemeProvider,
    BpnsSchemeProvider,
    BpnValidator,
)
from .onboarding_hooks import CatenaxProcedureHooks
from .policy_profile.compiler import CatenaxPolicyDialectProvider
from .purposes import CatenaxPurposeCatalogProvider
from .requirements import CatenaxRequirementProvider

_MANIFEST_PATH = pathlib.Path(__file__).parent / "manifest.toml"

with open(_MANIFEST_PATH, "rb") as _f:
    _MANIFEST_DATA = tomllib.load(_f)

MANIFEST: PackManifest = PackManifest.from_toml(_MANIFEST_PATH)

PROVIDERS: dict[PackCapability, Any] = {
    PackCapability.REQUIREMENT_PROVIDER: CatenaxRequirementProvider(),
    PackCapability.POLICY_DIALECT: CatenaxPolicyDialectProvider(),
    PackCapability.PURPOSE_CATALOG: CatenaxPurposeCatalogProvider(),
    PackCapability.IDENTIFIER_SCHEME: BpnlSchemeProvider(),
    PackCapability.CREDENTIAL_PROFILE: CatenaxCredentialProfileProvider(),
    PackCapability.PROCEDURE_HOOK: CatenaxProcedureHooks(),
    PackCapability.EVIDENCE_AUGMENTER: CatenaxEvidenceAugmenter(),
}

__all__ = [
    "MANIFEST",
    "PROVIDERS",
    "BpnlSchemeProvider",
    "BpnsSchemeProvider",
    "BpnaSchemeProvider",
    "BpnValidator",
    "CatenaxRequirementProvider",
    "CatenaxPolicyDialectProvider",
    "CatenaxPurposeCatalogProvider",
    "CatenaxCredentialProfileProvider",
    "CatenaxProcedureHooks",
    "CatenaxEvidenceAugmenter",
]
