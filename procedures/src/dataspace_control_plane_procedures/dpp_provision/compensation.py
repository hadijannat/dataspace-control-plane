"""Compensation orchestration for the dpp_provision procedure.

Runs compensation activities in reverse order of recorded actions.
Must be called only from inside a workflow function context.
"""
from __future__ import annotations

from temporalio import workflow

from .state import DppWorkflowState
from .activities import deregister_dpp, DeregisterDppInput


async def run_dpp_compensation(state: DppWorkflowState) -> None:
    """Deregister the DPP twin if it was registered before the failure."""
    from dataspace_control_plane_procedures._shared.activity_options import PROVISIONING_OPTIONS

    for marker in state.compensation.pending():
        if marker.action == "upsert_dpp_twin_data":
            await workflow.execute_activity(
                deregister_dpp,
                DeregisterDppInput(
                    tenant_id="",  # resolved from resource_id at runtime
                    dpp_id=marker.resource_id,
                ),
                **PROVISIONING_OPTIONS,
            )
            state.compensation.mark_compensated(
                marker.action,
                marker.resource_id,
                completed_at=workflow.now(),
            )
