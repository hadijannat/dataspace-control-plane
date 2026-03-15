from __future__ import annotations

from temporalio import workflow

from dataspace_control_plane_procedures.publish_asset.state import PublishAssetWorkflowState
from dataspace_control_plane_procedures.publish_asset.activities import (
    retract_asset_offer,
    RetractInput,
)
from dataspace_control_plane_procedures._shared.activity_options import PROVISIONING_OPTIONS


async def run_publish_compensation(state: PublishAssetWorkflowState, tenant_id: str) -> None:
    """Retract the asset offer from the catalog if it was already published."""
    for marker in state.compensation.pending():
        if marker.action == "asset_offer_published" and state.asset_offer_id:
            await workflow.execute_activity(
                retract_asset_offer,
                RetractInput(
                    tenant_id=tenant_id,
                    offer_id=state.asset_offer_id,
                    reason="compensation",
                ),
                **PROVISIONING_OPTIONS,
            )
            state.compensation.mark_compensated(
                marker.action,
                marker.resource_id,
                completed_at=workflow.now(),
            )
