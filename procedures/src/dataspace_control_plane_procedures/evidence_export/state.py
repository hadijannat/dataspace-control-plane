from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvidenceExportWorkflowState:
    # pending | collected | manifest_built | signed | stored | published
    phase: str = "pending"
    evidence_refs: list[str] = field(default_factory=list)
    bundle_ref: str = ""
    manifest_ref: str = ""
    signature_ref: str = ""
    export_url: str = ""
    is_dry_run: bool = False
    dry_run_diff: str = ""
