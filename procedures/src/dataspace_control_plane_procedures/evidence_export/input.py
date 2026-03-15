from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceExportStartInput:
    tenant_id: str
    legal_entity_id: str
    scope: str              # e.g. "contracts", "compliance", "full"
    period_start: str       # ISO8601
    period_end: str
    export_destination: str = ""
    dry_run: bool = False
    bundle_type: str = "quarterly"  # "monthly"|"quarterly"|"nightly"|"on_demand"
    idempotency_key: str = ""


@dataclass(frozen=True)
class EvidenceExportResult:
    workflow_id: str
    status: str
    bundle_ref: str = ""
    signature_ref: str = ""
    export_url: str = ""
    evidence_count: int = 0
    dry_run: bool = False


@dataclass
class EvidenceExportStatusQuery:
    phase: str
    evidence_count: int
    bundle_ref: str
    is_signed: bool
