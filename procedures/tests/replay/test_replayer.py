from __future__ import annotations

from datetime import timedelta
import uuid

import pytest
from temporalio.worker import Replayer, Worker

from dataspace_control_plane_procedures.company_onboarding.api import ALL_ACTIVITIES as ONBOARDING_ACTIVITIES
from dataspace_control_plane_procedures.company_onboarding.input import OnboardingStartInput
from dataspace_control_plane_procedures.company_onboarding.messages import ApproveCaseInput
from dataspace_control_plane_procedures.company_onboarding.workflow import CompanyOnboardingWorkflow
from dataspace_control_plane_procedures.connector_bootstrap.api import ALL_ACTIVITIES as CONNECTOR_ACTIVITIES
from dataspace_control_plane_procedures.connector_bootstrap.input import ConnectorStartInput
from dataspace_control_plane_procedures.connector_bootstrap.workflow import ConnectorBootstrapWorkflow
from dataspace_control_plane_procedures.negotiate_contract.api import ALL_ACTIVITIES as NEGOTIATION_ACTIVITIES
from dataspace_control_plane_procedures.negotiate_contract.input import NegotiationStartInput
from dataspace_control_plane_procedures.negotiate_contract.messages import CounterpartyAccepted
from dataspace_control_plane_procedures.negotiate_contract.workflow import NegotiateContractWorkflow
from dataspace_control_plane_procedures.rotate_credentials.api import ALL_ACTIVITIES as ROTATION_ACTIVITIES
from dataspace_control_plane_procedures.rotate_credentials.input import RotationStartInput
from dataspace_control_plane_procedures.rotate_credentials.messages import PauseRotation
from dataspace_control_plane_procedures.rotate_credentials.workflow import RotateCredentialsWorkflow


def unique_task_queue(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


@pytest.mark.asyncio
async def test_company_onboarding_history_replays(time_skipping_env) -> None:
    task_queue = unique_task_queue("replay-company")
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
                id="replay-company-onboarding",
                task_queue=task_queue,
            )
            await env.sleep(timedelta(seconds=1))
            await handle.execute_update("approve_case", ApproveCaseInput(reviewer_id="reviewer-1"))
            await handle.result()
            history = await handle.fetch_history()

    await Replayer(workflows=[CompanyOnboardingWorkflow]).replay_workflow(history)


@pytest.mark.asyncio
async def test_connector_bootstrap_history_replays(time_skipping_env) -> None:
    task_queue = unique_task_queue("replay-connector")

    async with time_skipping_env() as env:
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[ConnectorBootstrapWorkflow],
            activities=CONNECTOR_ACTIVITIES,
        ):
            handle = await env.client.start_workflow(
                ConnectorBootstrapWorkflow.run,
                ConnectorStartInput(
                    tenant_id="tenant-a",
                    legal_entity_id="legal-entity-a",
                    environment="test",
                    binding_name="primary",
                    connector_url="https://connector.example.test",
                    wallet_ref="wallet:test",
                ),
                id="replay-connector-bootstrap",
                task_queue=task_queue,
            )
            await handle.result()
            history = await handle.fetch_history()

    await Replayer(workflows=[ConnectorBootstrapWorkflow]).replay_workflow(history)


@pytest.mark.asyncio
async def test_negotiate_contract_history_replays(time_skipping_env) -> None:
    task_queue = unique_task_queue("replay-negotiate")

    async with time_skipping_env() as env:
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[NegotiateContractWorkflow],
            activities=NEGOTIATION_ACTIVITIES,
        ):
            handle = await env.client.start_workflow(
                NegotiateContractWorkflow.run,
                NegotiationStartInput(
                    tenant_id="tenant-a",
                    legal_entity_id="legal-entity-a",
                    offer_id="offer-1",
                    counterparty_connector_id="counterparty-1",
                    purpose="analytics",
                    asset_id="asset-1",
                    policy_template_id="policy-1",
                ),
                id="replay-negotiate-contract",
                task_queue=task_queue,
            )
            await env.sleep(timedelta(seconds=1))
            await handle.signal(
                "counterparty_accepted",
                CounterpartyAccepted(event_id="accept-1", negotiation_ref="negotiation-1"),
            )
            await handle.result()
            history = await handle.fetch_history()

    await Replayer(workflows=[NegotiateContractWorkflow]).replay_workflow(history)


@pytest.mark.asyncio
async def test_rotate_credentials_history_replays(time_skipping_env) -> None:
    task_queue = unique_task_queue("replay-rotate")

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
                ),
                id="replay-rotate-credentials",
                task_queue=task_queue,
            )
            await env.sleep(timedelta(seconds=1))
            await handle.execute_update("pause_rotation", PauseRotation(reviewer_id="reviewer-1"))
            await handle.terminate(reason="replay snapshot")
            history = await handle.fetch_history()

    await Replayer(workflows=[RotateCredentialsWorkflow]).replay_workflow(history)
