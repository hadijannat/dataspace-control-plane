"""Compensation orchestration for the delegate_tenant procedure.

Runs compensation activities in reverse order of recorded actions.
Must be called only from inside a workflow function context.
"""
from __future__ import annotations

from temporalio import workflow

from .state import DelegationWorkflowState
from .activities import (
    revoke_delegation,
    RevokeDelegationInput,
)


async def run_delegation_compensation(state: DelegationWorkflowState) -> None:
    """Execute compensation in reverse order of recorded actions."""
    from dataspace_control_plane_procedures._shared.activity_options import PROVISIONING_OPTIONS

    for marker in state.compensation.pending():
        if marker.action in ("apply_shared_connector_delegation", "create_child_topology"):
            await workflow.execute_activity(
                revoke_delegation,
                RevokeDelegationInput(
                    tenant_id="",          # caller should embed tenant_id in resource_id if needed
                    delegation_ref=marker.resource_id if marker.action == "apply_shared_connector_delegation" else "",
                    child_topology_ref=marker.resource_id if marker.action == "create_child_topology" else "",
                ),
                **PROVISIONING_OPTIONS,
            )
            state.compensation.mark_compensated(marker.action, marker.resource_id)
