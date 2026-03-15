from __future__ import annotations

from datetime import timedelta
import uuid

import pytest
from temporalio.client import WorkflowUpdateFailedError
from temporalio.worker import Worker

from dataspace_control_plane_procedures.company_onboarding.api import ALL_ACTIVITIES as ONBOARDING_ACTIVITIES
from dataspace_control_plane_procedures.company_onboarding.input import (
    OnboardingResult,
    OnboardingStartInput,
    OnboardingStatusQuery,
)
from dataspace_control_plane_procedures.company_onboarding.messages import (
    ApproveCaseInput,
    ApproveCaseResult,
)
from dataspace_control_plane_procedures.company_onboarding.workflow import CompanyOnboardingWorkflow
from dataspace_control_plane_procedures.rotate_credentials.api import ALL_ACTIVITIES as ROTATION_ACTIVITIES
from dataspace_control_plane_procedures.rotate_credentials.input import (
    RotationStartInput,
    RotationStatusQuery,
)
from dataspace_control_plane_procedures.rotate_credentials.messages import (
    PauseResult,
    PauseRotation,
    ResumeResult,
    ResumeRotation,
)
from dataspace_control_plane_procedures.rotate_credentials.workflow import RotateCredentialsWorkflow


def unique_task_queue(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


async def _wait_for_onboarding_phase(env, handle, phase: str) -> OnboardingStatusQuery:
    for _ in range(10):
        status = await handle.query("get_status", result_type=OnboardingStatusQuery)
        if status.phase == phase:
            return status
        await env.sleep(timedelta(seconds=1))
    raise AssertionError(f"workflow did not reach phase {phase!r}")


@pytest.mark.asyncio
async def test_company_onboarding_accepts_review_update_and_completes(time_skipping_env) -> None:
    task_queue = unique_task_queue("company-onboarding")
    start_input = OnboardingStartInput(
        tenant_id="tenant-a",
        legal_entity_id="legal-entity-a",
        legal_entity_name="Acme GmbH",
        bpnl="BPNL000000000001",
        jurisdiction="DE",
        contact_email="ops@example.com",
        connector_url="https://connector.example.test",
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
                start_input,
                id="company-onboarding:test",
                task_queue=task_queue,
            )

            status = await _wait_for_onboarding_phase(env, handle, "awaiting_approval")
            assert status.next_required_action == "approve"

            update_result = await handle.execute_update(
                "approve_case",
                ApproveCaseInput(reviewer_id="reviewer-1", notes="approved"),
                result_type=ApproveCaseResult,
            )
            assert update_result.accepted is True

            result = await handle.result()
            assert isinstance(result, OnboardingResult)
            assert result.status == "completed"
            assert result.registration_ref.startswith("reg:")


@pytest.mark.asyncio
async def test_rotate_credentials_rejects_resume_until_paused(time_skipping_env) -> None:
    task_queue = unique_task_queue("rotate-credentials")

    async with time_skipping_env() as env:
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[RotateCredentialsWorkflow],
            activities=ROTATION_ACTIVITIES,
        ):
            handle = await env.client.start_workflow(
                RotateCredentialsWorkflow.run,
                RotationStartInput(
                    tenant_id="tenant-a",
                    legal_entity_id="legal-entity-a",
                    credential_profile="default",
                    rotation_interval_days=30,
                    look_ahead_days=15,
                ),
                id="rotate-credentials:test",
                task_queue=task_queue,
            )

            await env.sleep(timedelta(seconds=1))

            with pytest.raises(WorkflowUpdateFailedError):
                await handle.execute_update(
                    "resume_rotation",
                    ResumeRotation(reviewer_id="reviewer-1"),
                    result_type=ResumeResult,
                )

            pause_result = await handle.execute_update(
                "pause_rotation",
                PauseRotation(reviewer_id="reviewer-1"),
                result_type=PauseResult,
            )
            assert pause_result.accepted is True

            paused_status = await handle.query("get_status", result_type=RotationStatusQuery)
            assert paused_status.is_paused is True

            resume_result = await handle.execute_update(
                "resume_rotation",
                ResumeRotation(reviewer_id="reviewer-1", notes="resume"),
                result_type=ResumeResult,
            )
            assert resume_result.accepted is True

            resumed_status = await handle.query("get_status", result_type=RotationStatusQuery)
            assert resumed_status.is_paused is False

            await handle.terminate(reason="test cleanup")
