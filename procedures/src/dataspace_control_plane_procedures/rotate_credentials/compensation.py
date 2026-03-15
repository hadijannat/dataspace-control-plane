"""Compensation logic for rotate_credentials — retires newly issued credentials
if binding update fails, preventing credential leakage.
"""
from __future__ import annotations

from temporalio import workflow

from dataspace_control_plane_procedures._shared.activity_options import PROVISIONING_OPTIONS

from .state import RotationWorkflowState


async def run_rotation_compensation(
    state: RotationWorkflowState,
    tenant_id: str,
    legal_entity_id: str,
) -> None:
    """Retire newly issued credentials when the binding update step fails.

    This is the rollback path: if we successfully reissued credentials but could
    not update connector/wallet bindings, we retire the new credentials so they
    don't accumulate as orphaned issuances in the trust domain.

    No-ops when there are no new credentials to retire.
    """
    if not state.new_credential_ids:
        return

    from .activities import retire_new_credentials_on_failure, RetireNewCredentialsInput

    await workflow.execute_activity(
        retire_new_credentials_on_failure,
        RetireNewCredentialsInput(
            tenant_id=tenant_id,
            legal_entity_id=legal_entity_id,
            new_credential_ids=list(state.new_credential_ids),
        ),
        **PROVISIONING_OPTIONS,
    )

    state.compensation.mark_compensated(
        action="credential_reissuance",
        resource_id=f"{tenant_id}:{legal_entity_id}",
        completed_at=workflow.now(),
    )
