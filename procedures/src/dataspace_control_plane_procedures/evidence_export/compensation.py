"""Evidence export is append-only; no compensation is needed."""
from .state import EvidenceExportWorkflowState


async def run_evidence_export_compensation(state: EvidenceExportWorkflowState) -> None:
    pass
