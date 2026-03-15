"""Pack capability declarations.

A pack declares which capability interfaces it implements via its manifest.
The registry resolves packs by capability, not by concrete class.
"""
from __future__ import annotations

from enum import Enum


class PackCapability(str, Enum):
    """Enumeration of all capability slots a pack may fill.

    A pack may implement any subset of these. The registry groups registered
    packs by capability so callers can say "give me all RequirementProviders
    active for this tenant" without knowing concrete pack names.
    """

    REQUIREMENT_PROVIDER = "RequirementProvider"
    POLICY_DIALECT = "PolicyDialectProvider"
    PURPOSE_CATALOG = "PurposeCatalogProvider"
    IDENTIFIER_SCHEME = "IdentifierSchemeProvider"
    CREDENTIAL_PROFILE = "CredentialProfileProvider"
    TRUST_ANCHOR_OVERLAY = "TrustAnchorOverlayProvider"
    TWIN_TEMPLATE = "TwinTemplateProvider"
    PROCEDURE_HOOK = "ProcedureHookProvider"
    EVIDENCE_AUGMENTER = "EvidenceAugmenter"
    UI_SCHEMA = "UiSchemaProvider"
    PACK_MIGRATION = "PackMigrationProvider"
    DATA_EXCHANGE_PROFILE = "DataExchangeProfileProvider"
    LIFECYCLE_MODEL = "LifecycleModelProvider"
    DELEGATED_ACT = "DelegatedActProvider"
