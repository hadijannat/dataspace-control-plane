from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dataspace_control_plane_procedures.company_onboarding.activities import (
    CompensateConnectorBootstrapInput,
    CompensateRegistrationInput,
    CompensateWalletBootstrapInput,
    HierarchyInput,
    HierarchyResult,
)
from dataspace_control_plane_procedures.company_onboarding.compensation import run_compensation
from dataspace_control_plane_procedures.company_onboarding.input import OnboardingStartInput
from dataspace_control_plane_procedures.company_onboarding.state import OnboardingWorkflowState
from dataspace_control_plane_procedures.company_onboarding.workflow import CompanyOnboardingWorkflow


@pytest.mark.asyncio
async def test_bind_hierarchy_passes_parent_bpnl_and_sets_bound_phase(monkeypatch) -> None:
    seen_inputs: list[HierarchyInput] = []

    async def _fake_execute_activity(fn, inp, **kwargs):
        seen_inputs.append(inp)
        return HierarchyResult(bound=True, parent_bpnl=inp.parent_bpnl)

    monkeypatch.setattr(
        "dataspace_control_plane_procedures.company_onboarding.workflow.workflow.execute_activity",
        _fake_execute_activity,
    )

    workflow = CompanyOnboardingWorkflow()
    await workflow._bind_hierarchy(
        OnboardingStartInput(
            tenant_id="tenant-a",
            legal_entity_id="lei-1",
            legal_entity_name="Acme GmbH",
            bpnl="BPNL000000000001",
            jurisdiction="DE",
            contact_email="ops@example.com",
            connector_url="https://connector.example.test",
            parent_bpnl="BPNL000000000999",
        )
    )

    assert workflow._state.phase == "hierarchy_bound"
    assert seen_inputs[0].parent_bpnl == "BPNL000000000999"


@pytest.mark.asyncio
async def test_bind_hierarchy_skips_when_parent_bpnl_absent(monkeypatch) -> None:
    async def _fail_execute_activity(*args, **kwargs):
        raise AssertionError("bind_hierarchy activity should not be called when parent_bpnl is absent")

    monkeypatch.setattr(
        "dataspace_control_plane_procedures.company_onboarding.workflow.workflow.execute_activity",
        _fail_execute_activity,
    )

    workflow = CompanyOnboardingWorkflow()
    await workflow._bind_hierarchy(
        OnboardingStartInput(
            tenant_id="tenant-a",
            legal_entity_id="lei-1",
            legal_entity_name="Acme GmbH",
            bpnl="BPNL000000000001",
            jurisdiction="DE",
            contact_email="ops@example.com",
            connector_url="https://connector.example.test",
        )
    )

    assert workflow._state.phase == "hierarchy_skipped"


@pytest.mark.asyncio
async def test_run_compensation_rolls_back_connector_wallet_and_registration(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    async def _fake_execute_activity(fn, inp, **kwargs):
        if isinstance(inp, CompensateConnectorBootstrapInput):
            calls.append(("connector", inp.connector_binding_id))
        elif isinstance(inp, CompensateWalletBootstrapInput):
            calls.append(("wallet", inp.wallet_ref))
        elif isinstance(inp, CompensateRegistrationInput):
            calls.append(("registration", inp.registration_ref))

    monkeypatch.setattr(
        "dataspace_control_plane_procedures.company_onboarding.compensation.workflow.execute_activity",
        _fake_execute_activity,
    )
    monkeypatch.setattr(
        "dataspace_control_plane_procedures.company_onboarding.compensation.workflow.now",
        lambda: datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    state = OnboardingWorkflowState(
        registration_ref="reg:tenant-a:lei-1",
        wallet_ref="wallet:tenant-a:lei-1",
        connector_ref="connector:tenant-a:lei-1",
    )
    state.compensation.record("register_legal_entity", state.registration_ref)
    state.compensation.record("bootstrap_wallet", state.wallet_ref)
    state.compensation.record("bootstrap_connector", state.connector_ref)

    await run_compensation(state)

    assert calls == [
        ("connector", "connector:tenant-a:lei-1"),
        ("wallet", "wallet:tenant-a:lei-1"),
        ("registration", "reg:tenant-a:lei-1"),
    ]
