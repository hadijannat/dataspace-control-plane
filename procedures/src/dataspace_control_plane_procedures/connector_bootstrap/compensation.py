"""Compensation orchestration for the connector_bootstrap procedure.

Runs compensation activities in reverse order of recorded actions.
Must be called only from inside a workflow function context.
"""
from __future__ import annotations

from temporalio import workflow

from .state import ConnectorWorkflowState
from .activities import decommission_connector, DecommissionInput


async def run_connector_compensation(state: ConnectorWorkflowState) -> None:
    """Execute compensation in reverse order of recorded actions.

    Compensates in reverse registration order:
      1. Dataspace registration (deregister from DSP catalog)
      2. Infra apply (destroy provisioned infra)
    """
    from dataspace_control_plane_procedures._shared.activity_options import PROVISIONING_OPTIONS

    for marker in state.compensation.pending():
        if marker.action in ("apply_connector_infra", "register_in_dataspace"):
            await workflow.execute_activity(
                decommission_connector,
                DecommissionInput(
                    connector_binding_id=state.connector_binding_id,
                    infra_apply_ref=state.infra_apply_ref if marker.action == "apply_connector_infra" else "",
                    dataspace_connector_id=(
                        state.dataspace_connector_id if marker.action == "register_in_dataspace" else ""
                    ),
                ),
                **PROVISIONING_OPTIONS,
            )
            state.compensation.mark_compensated(
                marker.action,
                marker.resource_id,
                completed_at=workflow.now(),
            )
