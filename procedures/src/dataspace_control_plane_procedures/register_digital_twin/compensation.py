from __future__ import annotations

from temporalio import workflow

from dataspace_control_plane_procedures.register_digital_twin.state import TwinWorkflowState
from dataspace_control_plane_procedures.register_digital_twin.activities import (
    deregister_shell,
    DeregisterInput,
)
from dataspace_control_plane_procedures._shared.activity_options import PROVISIONING_OPTIONS


async def run_twin_compensation(state: TwinWorkflowState, tenant_id: str) -> None:
    """Deregister shell and submodels in reverse order."""
    _COVERED_ACTIONS = frozenset(
        ("upsert_aas_shell", "shell_upserted", "submodels_upserted", "registry_registered")
    )
    covered_markers = [m for m in state.compensation.pending() if m.action in _COVERED_ACTIONS]
    if covered_markers and state.shell_id:
        await workflow.execute_activity(
            deregister_shell,
            DeregisterInput(
                tenant_id=tenant_id,
                shell_id=state.shell_id,
                submodel_ids=list(state.submodel_ids),
                reason="compensation",
            ),
            **PROVISIONING_OPTIONS,
        )
        completed_at = workflow.now()
        for marker in covered_markers:
            state.compensation.mark_compensated(
                marker.action,
                marker.resource_id,
                completed_at=completed_at,
            )
