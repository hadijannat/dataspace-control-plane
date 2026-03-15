"""Revocation is not reversible — evidence is append-only."""
from .state import RevocationWorkflowState


async def run_revocation_compensation(state: RevocationWorkflowState) -> None:
    pass
