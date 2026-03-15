"""
Canonical AAS/twin models — normalized AAS Release 25-01 references.
No raw AAS API payloads; only key references and normalized metadata.
"""
from __future__ import annotations
from pydantic import field_validator

from .common import CanonicalBase


class SemanticId(CanonicalBase):
    """Normalized semantic ID reference (IRI or compact form)."""
    value: str  # e.g. "https://admin-shell.io/DataSpecificationIec61360/3/0"
    type: str = "ExternalReference"


class EndpointRef(CanonicalBase):
    """Normalized endpoint reference from an AAS descriptor."""
    interface: str   # e.g. "SUBMODEL-3.0"
    protocol: str    # e.g. "HTTP"
    href: str        # endpoint URL


class SubmodelRef(CanonicalBase):
    """Reference to a submodel by ID and semantic class."""
    submodel_id: str
    semantic_class: SemanticId | None = None


class SubmodelDescriptorRef(CanonicalBase):
    """Normalized submodel descriptor (from DTR / AAS Registry)."""
    submodel_id: str
    semantic_class: SemanticId | None = None
    endpoints: list[EndpointRef] = []


class AasShellRef(CanonicalBase):
    """Reference to an AAS Shell by global asset ID."""
    global_asset_id: str
    shell_id: str | None = None
    submodel_refs: list[SubmodelRef] = []


class DataSpecificationRef(CanonicalBase):
    """Reference to a data specification template (e.g. IEC 61360)."""
    uri: str


class AasAccessRuleRef(CanonicalBase):
    """Normalized reference to an AAS access rule (AAS Part 4 Security)."""
    rule_id: str
    policy_ref: str      # Points to a CanonicalPolicy.policy_id
    object_ref: str      # AAS object this rule applies to


class TwinArtifactRef(CanonicalBase):
    """Reference to a packaged twin artifact (AASX or JSON bundle)."""
    artifact_id: str
    format: str    # "aasx" | "json"
    storage_uri: str
    checksum: str | None = None
