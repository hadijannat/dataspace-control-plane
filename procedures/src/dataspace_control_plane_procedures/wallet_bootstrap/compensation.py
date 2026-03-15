from __future__ import annotations

from temporalio import workflow

from dataspace_control_plane_procedures.wallet_bootstrap.state import WalletWorkflowState
from dataspace_control_plane_procedures.wallet_bootstrap.activities import (
    decommission_wallet,
    DecommissionWalletInput,
)
from dataspace_control_plane_procedures._shared.activity_options import PROVISIONING_OPTIONS


async def run_wallet_compensation(state: WalletWorkflowState, tenant_id: str) -> None:
    """Decommission wallet and deregister DID in reverse order."""
    for marker in state.compensation.pending():
        if marker.action == "wallet_created" and state.wallet_ref:
            await workflow.execute_activity(
                decommission_wallet,
                DecommissionWalletInput(
                    tenant_id=tenant_id,
                    wallet_ref=state.wallet_ref,
                    wallet_did=state.wallet_did,
                    reason="compensation",
                ),
                **PROVISIONING_OPTIONS,
            )
            state.compensation.mark_compensated(marker.action, marker.resource_id)
