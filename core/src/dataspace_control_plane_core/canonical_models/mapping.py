"""Canonical schema mapping models — first-mile semantic bridge."""
from __future__ import annotations
from pydantic import field_validator

from .common import CanonicalBase


class SourceSchemaRef(CanonicalBase):
    """Reference to a source schema (ERP field, PLM export, IoT stream)."""
    schema_id: str
    system_type: str       # e.g. "sap_erp", "catia_plm", "opcua"
    field_path: str        # Dot-separated path in the source schema


class TargetSemanticRef(CanonicalBase):
    """Reference to a target semantic field in a canonical or AAS model."""
    semantic_id: str       # IRI or compact form
    submodel_id: str | None = None
    property_path: str     # Dot-separated path in the target model


class TransformStep(CanonicalBase):
    """A single transform step in a mapping pipeline."""
    step_type: str         # e.g. "unit_conversion", "regex_extract", "lookup", "expression"
    config: dict           # Step-specific configuration


class FieldMapping(CanonicalBase):
    """Maps one source field to one target semantic field via transform steps."""
    mapping_id: str
    source: SourceSchemaRef
    target: TargetSemanticRef
    transforms: list[TransformStep] = []
    confidence: float = 1.0  # 0.0–1.0; < 1.0 means AI suggestion, pending review
    rationale: str | None = None  # Explanation from LLM or human reviewer


class LineageEdge(CanonicalBase):
    """A lineage link between source field and target field in the lineage graph."""
    source_field: str
    target_field: str
    mapping_id: str


class ConfidenceScore(CanonicalBase):
    """Confidence score attached to an AI mapping suggestion."""
    score: float           # 0.0–1.0
    method: str            # e.g. "llm_cosine", "rule_based", "human_review"
    explanation: str | None = None
