"""Compensation orchestration for the negotiate_contract procedure.

Runs compensation activities in reverse order of recorded actions.
Must be called only from inside a workflow function context.
"""
from __future__ import annotations

from temporalio import workflow

from .state import NegotiationWorkflowState
from .activities import cancel_negotiation, CancelInput


async def run_negotiation_compensation(state: NegotiationWorkflowState) -> None:
    """Cancel the negotiation if it was started but not yet concluded."""
    from dataspace_control_plane_procedures._shared.activity_options import EXTERNAL_CALL_OPTIONS

    for marker in state.compensation.pending():
        if marker.action == "start_dsp_negotiation":
            await workflow.execute_activity(
                cancel_negotiation,
                CancelInput(
                    tenant_id="",  # resolved from resource_id at runtime
                    negotiation_ref=marker.resource_id,
                    reason="workflow compensation",
                ),
                **EXTERNAL_CALL_OPTIONS,
            )
            state.compensation.mark_compensated(
                marker.action,
                marker.resource_id,
                completed_at=workflow.now(),
            )
