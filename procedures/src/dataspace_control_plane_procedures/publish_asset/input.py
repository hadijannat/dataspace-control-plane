from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PublishAssetStartInput:
    tenant_id: str
    legal_entity_id: str
    asset_binding_id: str
    revision: str
    global_asset_id: str
    source_schema_id: str
    policy_template_id: str
    pack_id: str = "default"
    force_republish: bool = False
    idempotency_key: str = ""


@dataclass
class PublishAssetResult:
    workflow_id: str
    status: str
    asset_offer_id: str = ""
    discoverability_url: str = ""
    evidence_ref: str = ""


@dataclass
class PublishAssetStatusQuery:
    phase: str
    asset_offer_id: str
    is_visible: bool
    blocking_reason: str
