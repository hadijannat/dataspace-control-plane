from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TwinStartInput:
    tenant_id: str
    legal_entity_id: str
    aas_id: str
    revision: str
    global_asset_id: str
    shell_descriptor: dict  # raw AAS descriptor
    submodel_refs: list[dict]
    semantic_id: str = ""
    pack_id: str = "default"


@dataclass
class TwinResult:
    workflow_id: str
    status: str
    shell_id: str = ""
    registry_url: str = ""
    evidence_ref: str = ""


@dataclass
class TwinStatusQuery:
    phase: str
    shell_id: str
    submodel_count: int
    registry_registered: bool
    access_bound: bool
    blocking_reason: str
