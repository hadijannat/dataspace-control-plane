"""Public import surface for the packs layer."""
from __future__ import annotations

from ._shared.capabilities import PackCapability
from ._shared.errors import (
    NormativeSourceError,
    PackActivationError,
    PackConflictError,
    PackDependencyError,
    PackError,
    PackNotFoundError,
    PackProvenanceError,
    PackValidationError,
    PackVersionError,
    RuleNotFoundError,
)
from ._shared.interfaces import (
    CredentialProfileProvider,
    DataExchangeProfileProvider,
    EvidenceAugmenter,
    IdentifierSchemeProvider,
    LifecycleModelProvider,
    PackMigrationProvider,
    PolicyDialectProvider,
    ProcedureHookProvider,
    PurposeCatalogProvider,
    RequirementProvider,
    TrustAnchorOverlayProvider,
    TwinTemplateProvider,
    UiSchemaProvider,
)
from ._shared.manifest import PackCapabilityDecl, PackDependency, PackManifest
from ._shared.provenance import ArtifactProvenance, NormativeSource
from ._shared.reducers import (
    check_override_safety,
    reduce_defaults,
    reduce_evidence,
    reduce_identifier_schemes,
    reduce_policy_compiler,
    reduce_validation,
)
from ._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult
from ._shared.versioning import SemVer, versions_compatible
from .activation import ActivationRequest, PackActivationManager
from .loader import load_all_builtin_packs, load_pack
from .registry import PackRegistry, get_registry, reset_registry
from .resolver import PackResolver, ResolvedPackProfile

__all__ = [
    # Registry
    "PackRegistry",
    "get_registry",
    "reset_registry",
    # Loader
    "load_pack",
    "load_all_builtin_packs",
    # Resolver
    "PackResolver",
    "ResolvedPackProfile",
    # Activation
    "ActivationRequest",
    "PackActivationManager",
    # Manifest
    "PackManifest",
    "PackDependency",
    "PackCapabilityDecl",
    # Capabilities
    "PackCapability",
    # Rule model
    "RuleDefinition",
    "RuleViolation",
    "ValidationResult",
    # Provenance
    "ArtifactProvenance",
    "NormativeSource",
    # Interfaces
    "RequirementProvider",
    "PolicyDialectProvider",
    "PurposeCatalogProvider",
    "IdentifierSchemeProvider",
    "CredentialProfileProvider",
    "TrustAnchorOverlayProvider",
    "TwinTemplateProvider",
    "ProcedureHookProvider",
    "EvidenceAugmenter",
    "UiSchemaProvider",
    "PackMigrationProvider",
    "DataExchangeProfileProvider",
    "LifecycleModelProvider",
    # Reducers
    "reduce_validation",
    "reduce_evidence",
    "reduce_policy_compiler",
    "reduce_identifier_schemes",
    "reduce_defaults",
    "check_override_safety",
    # Versioning
    "SemVer",
    "versions_compatible",
    # Errors
    "PackError",
    "PackNotFoundError",
    "PackConflictError",
    "PackDependencyError",
    "PackVersionError",
    "PackValidationError",
    "PackActivationError",
    "PackProvenanceError",
    "RuleNotFoundError",
    "NormativeSourceError",
]
