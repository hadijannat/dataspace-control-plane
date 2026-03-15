from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DppStartInput:
    tenant_id: str
    legal_entity_id: str
    product_instance_id: str
    revision: str
    source_system_ref: str
    submodel_template_ids: list[str]
    asset_id: str = ""
    pack_id: str = "default"


@dataclass
class DppResult:
    workflow_id: str
    status: str
    dpp_id: str = ""
    identifier_link: str = ""
    evidence_ref: str = ""


@dataclass
class DppStatusQuery:
    phase: str
    dpp_id: str
    completeness_score: float
    is_published: bool
    blocking_reason: str
