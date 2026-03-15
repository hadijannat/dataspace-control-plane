from __future__ import annotations

from datetime import datetime, timezone

import pytest
from temporalio.testing import ActivityEnvironment

from dataspace_control_plane_procedures._shared.compensation import CompensationLog
from dataspace_control_plane_procedures._shared.continue_as_new import CarryEnvelope, unwrap_start_input
from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.search_attributes import EXTERNAL_REFERENCE
from dataspace_control_plane_procedures.connector_bootstrap.activities import (
    ConnectorHealthInput,
    wait_for_runtime_healthy,
)
from dataspace_control_plane_procedures.registry import (
    ACTIVITY_REGISTRY,
    WORKFLOW_REGISTRY,
    populate_from_procedures,
    reset_registry,
)


def test_manual_review_state_round_trips_without_wall_clock_access() -> None:
    requested_at = datetime(2026, 3, 15, 9, 30, tzinfo=timezone.utc)
    decided_at = datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc)

    state = ManualReviewState()
    state.request("awaiting approval", "review-1", requested_at=requested_at)
    state.record_decision("approved", "reviewer-1", "ok", decided_at=decided_at)

    restored = ManualReviewState.from_snapshot(state.snapshot())

    assert restored.requested_at == requested_at
    assert restored.decided_at == decided_at
    assert restored.decision == "approved"


def test_compensation_log_snapshot_round_trips() -> None:
    completed_at = datetime(2026, 3, 15, 10, 30, tzinfo=timezone.utc)

    log = CompensationLog()
    log.record("register_legal_entity", "reg-1")
    log.record("register_in_dataspace", "dsp-1")
    log.mark_compensated("register_legal_entity", "reg-1", completed_at=completed_at)

    restored = CompensationLog.from_snapshot(log.snapshot())

    pending = restored.pending()
    assert len(pending) == 1
    assert pending[0].resource_id == "dsp-1"


def test_continue_as_new_envelope_preserves_start_input() -> None:
    start_input = {"tenant_id": "tenant-a"}
    state = {"phase": "awaiting_approval"}

    unwrapped_input, carry_state = unwrap_start_input(
        CarryEnvelope(start_input=start_input, state=state)
    )

    assert unwrapped_input == start_input
    assert carry_state == state


def test_external_reference_uses_exact_match_keyword_indexing() -> None:
    assert EXTERNAL_REFERENCE.indexed_value_type.name == "KEYWORD"


def test_registry_population_is_idempotent() -> None:
    reset_registry()
    populate_from_procedures()
    first_counts = (
        sum(len(workflows) for workflows in WORKFLOW_REGISTRY.values()),
        sum(len(activities) for activities in ACTIVITY_REGISTRY.values()),
    )

    populate_from_procedures()
    second_counts = (
        sum(len(workflows) for workflows in WORKFLOW_REGISTRY.values()),
        sum(len(activities) for activities in ACTIVITY_REGISTRY.values()),
    )

    assert first_counts == second_counts


@pytest.mark.asyncio
async def test_activity_environment_captures_heartbeats() -> None:
    env = ActivityEnvironment()
    heartbeats: list[tuple[object, ...]] = []
    env.on_heartbeat = lambda *details: heartbeats.append(details)

    result = await env.run(
        wait_for_runtime_healthy,
        ConnectorHealthInput(
            connector_url="https://connector.example.test",
            connector_binding_id="connector:test",
            max_polls=1,
        ),
    )

    assert result.is_healthy is True
    assert heartbeats
