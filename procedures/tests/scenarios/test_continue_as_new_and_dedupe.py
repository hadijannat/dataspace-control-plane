from __future__ import annotations

from datetime import timedelta
import uuid

import pytest
from temporalio.worker import Worker

from dataspace_control_plane_procedures._shared.compensation import CompensationMarker
from dataspace_control_plane_procedures._shared.continue_as_new import CarryEnvelope
from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures.company_onboarding.api import ALL_ACTIVITIES as ONBOARDING_ACTIVITIES
from dataspace_control_plane_procedures.company_onboarding.input import (
    OnboardingCarryState,
    OnboardingResult,
    OnboardingStartInput,
    OnboardingStatusQuery,
)
from dataspace_control_plane_procedures.company_onboarding.messages import (
    ApproveCaseInput,
    ApproveCaseResult,
    ExternalApprovalEvent,
)
from dataspace_control_plane_procedures.company_onboarding.workflow import CompanyOnboardingWorkflow


def unique_task_queue(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


@pytest.mark.asyncio
async def test_company_onboarding_carry_state_preserves_dedupe_ids(time_skipping_env) -> None:
    task_queue = unique_task_queue("company-onboarding-carry")
    start_input = OnboardingStartInput(
        tenant_id="tenant-a",
        legal_entity_id="legal-entity-a",
        legal_entity_name="Acme GmbH",
        bpnl="BPNL000000000001",
        jurisdiction="DE",
        contact_email="ops@example.com",
        connector_url="https://connector.example.test",
    )
    carry_state = OnboardingCarryState(
        phase="awaiting_approval",
        registration_ref="reg:tenant-a:legal-entity-a",
        approval_ref="approval:tenant-a:reg:tenant-a:legal-entity-a",
        bpnl=start_input.bpnl,
        wallet_ref="",
        connector_ref="",
        compliance_ref="",
        dedupe_ids={"approval-evt-1"},
        manual_review=ManualReviewState(
            is_pending=True,
            review_id="approval:tenant-a:reg:tenant-a:legal-entity-a",
            blocking_reason="awaiting operator approval",
        ),
        compensation_markers=[
            CompensationMarker(
                action="register_legal_entity",
                resource_id="reg:tenant-a:legal-entity-a",
            )
        ],
        iteration=1,
    )

    async with time_skipping_env() as env:
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[CompanyOnboardingWorkflow],
            activities=ONBOARDING_ACTIVITIES,
        ):
            handle = await env.client.start_workflow(
                CompanyOnboardingWorkflow.run,
                CarryEnvelope(start_input=start_input, state=carry_state),
                id="company-onboarding:carry",
                task_queue=task_queue,
            )

            initial_status = await handle.query("get_status", result_type=OnboardingStatusQuery)
            assert initial_status.phase == "awaiting_approval"

            await handle.signal(
                "external_approval_event",
                ExternalApprovalEvent(event_id="approval-evt-1", approved=True),
            )
            await env.sleep(timedelta(seconds=1))

            status_after_duplicate = await handle.query("get_status", result_type=OnboardingStatusQuery)
            assert status_after_duplicate.phase == "awaiting_approval"
            assert status_after_duplicate.next_required_action == "approve"

            update_result = await handle.execute_update(
                "approve_case",
                ApproveCaseInput(reviewer_id="reviewer-1", notes="approved"),
                result_type=ApproveCaseResult,
            )
            assert update_result.accepted is True

            result = await handle.result()
            assert isinstance(result, OnboardingResult)
            assert result.status == "completed"
