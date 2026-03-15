from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from temporalio.testing import ActivityEnvironment

from dataspace_control_plane_procedures._shared.compensation import CompensationLog
from dataspace_control_plane_procedures._shared.continue_as_new import (
    HISTORY_THRESHOLD,
    CarryEnvelope,
    DedupeState,
    coerce_workflow_input,
    decode_start_input,
    should_continue_as_new,
    unwrap_start_input,
)
from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.search_attributes import (
    EXTERNAL_REFERENCE,
    STATUS,
    TENANT_ID,
    build_search_attribute_updates,
)
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


# ---------------------------------------------------------------------------
# Minimal dataclasses used only in unit tests; no dependency on production
# workflow types so tests remain fast and import-clean.
# ---------------------------------------------------------------------------

@dataclass
class _SampleInput:
    tenant_id: str
    count: int = 0


@dataclass
class _SampleState:
    phase: str = ""


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


# ---------------------------------------------------------------------------
# should_continue_as_new
# ---------------------------------------------------------------------------


def test_should_continue_as_new_false_below_threshold() -> None:
    assert should_continue_as_new(HISTORY_THRESHOLD - 1) is False


def test_should_continue_as_new_true_at_threshold() -> None:
    assert should_continue_as_new(HISTORY_THRESHOLD) is True


def test_should_continue_as_new_true_above_threshold() -> None:
    assert should_continue_as_new(HISTORY_THRESHOLD + 100) is True


def test_should_continue_as_new_respects_custom_threshold() -> None:
    assert should_continue_as_new(50, threshold=100) is False
    assert should_continue_as_new(100, threshold=100) is True


# ---------------------------------------------------------------------------
# unwrap_start_input — plain (non-CarryEnvelope) path
# ---------------------------------------------------------------------------


def test_unwrap_start_input_plain_returns_none_carry_state() -> None:
    plain = _SampleInput(tenant_id="tenant-plain")
    unwrapped, carry = unwrap_start_input(plain)
    assert unwrapped is plain
    assert carry is None


# ---------------------------------------------------------------------------
# coerce_workflow_input
# ---------------------------------------------------------------------------


def test_coerce_workflow_input_returns_existing_instance_unchanged() -> None:
    original = _SampleInput(tenant_id="tenant-orig", count=7)
    coerced = coerce_workflow_input(original, _SampleInput)
    assert coerced is original


def test_coerce_workflow_input_converts_dict_to_target_type() -> None:
    coerced = coerce_workflow_input({"tenant_id": "tenant-dict", "count": 3}, _SampleInput)
    assert isinstance(coerced, _SampleInput)
    assert coerced.tenant_id == "tenant-dict"
    assert coerced.count == 3


# ---------------------------------------------------------------------------
# decode_start_input — all four paths
# ---------------------------------------------------------------------------


def test_decode_start_input_fresh_input_returns_none_state() -> None:
    fresh = _SampleInput(tenant_id="tenant-fresh", count=1)
    start, state = decode_start_input(fresh, start_input_type=_SampleInput, state_type=_SampleState)
    assert start == fresh
    assert state is None


def test_decode_start_input_carry_envelope_decodes_both_parts() -> None:
    si = _SampleInput(tenant_id="tenant-env", count=2)
    ss = _SampleState(phase="running")
    envelope = CarryEnvelope(start_input=si, state=ss)
    start, state = decode_start_input(envelope, start_input_type=_SampleInput, state_type=_SampleState)
    assert isinstance(start, _SampleInput)
    assert start.tenant_id == "tenant-env"
    assert isinstance(state, _SampleState)
    assert state.phase == "running"


def test_decode_start_input_raw_dict_envelope_decodes_both_parts() -> None:
    raw = {
        "start_input": {"tenant_id": "tenant-dict", "count": 5},
        "state": {"phase": "awaiting_approval"},
    }
    start, state = decode_start_input(raw, start_input_type=_SampleInput, state_type=_SampleState)
    assert isinstance(start, _SampleInput)
    assert start.tenant_id == "tenant-dict"
    assert isinstance(state, _SampleState)
    assert state.phase == "awaiting_approval"


def test_decode_start_input_dict_without_envelope_keys_treated_as_fresh() -> None:
    # A plain dict that does NOT have both 'start_input' and 'state' keys is
    # treated as a fresh start input to be coerced directly.
    raw = {"tenant_id": "tenant-plain-dict", "count": 9}
    start, state = decode_start_input(raw, start_input_type=_SampleInput, state_type=_SampleState)
    assert isinstance(start, _SampleInput)
    assert start.tenant_id == "tenant-plain-dict"
    assert state is None


# ---------------------------------------------------------------------------
# DedupeState
# ---------------------------------------------------------------------------


def test_dedupe_state_is_duplicate_false_before_mark() -> None:
    d = DedupeState()
    assert d.is_duplicate("msg-1") is False


def test_dedupe_state_is_duplicate_true_after_mark() -> None:
    d = DedupeState()
    d.mark_handled("msg-1")
    assert d.is_duplicate("msg-1") is True
    assert d.is_duplicate("msg-2") is False


def test_dedupe_state_snapshot_and_from_snapshot_round_trip() -> None:
    d = DedupeState()
    d.mark_handled("msg-a")
    d.mark_handled("msg-b")
    snap = d.snapshot()
    restored = DedupeState.from_snapshot(snap)
    assert restored.is_duplicate("msg-a") is True
    assert restored.is_duplicate("msg-b") is True
    assert restored.is_duplicate("msg-c") is False


def test_dedupe_state_snapshot_is_independent_copy() -> None:
    d = DedupeState()
    d.mark_handled("msg-1")
    snap = d.snapshot()
    # Mutating the original after snapshotting must not alter the snapshot.
    d.mark_handled("msg-2")
    assert "msg-2" not in snap


def test_dedupe_state_evicts_oldest_half_when_full() -> None:
    max_size = 6
    d = DedupeState(max_size=max_size)
    for i in range(max_size):
        d.mark_handled(f"msg-{i}")
    assert len(d._handled) == max_size
    # Adding one more triggers eviction: half the entries are dropped.
    d.mark_handled("msg-overflow")
    assert len(d._handled) < max_size
    # The newly added message must always survive eviction.
    assert d.is_duplicate("msg-overflow") is True


# ---------------------------------------------------------------------------
# ManualReviewState — additional paths
# ---------------------------------------------------------------------------


def test_manual_review_state_from_snapshot_none_returns_default() -> None:
    state = ManualReviewState.from_snapshot(None)
    assert state.is_pending is False
    assert state.decision is None
    assert state.requested_at is None


def test_manual_review_state_request_without_requested_at_leaves_none() -> None:
    state = ManualReviewState()
    state.request("needs approval", "review-2")
    assert state.is_pending is True
    assert state.blocking_reason == "needs approval"
    assert state.requested_at is None


def test_manual_review_state_is_approved_property() -> None:
    state = ManualReviewState()
    state.request("pending", "review-3")
    assert state.is_approved is False
    state.record_decision("approved", "reviewer-a", "looks good")
    assert state.is_approved is True
    assert state.is_rejected is False


def test_manual_review_state_is_rejected_property() -> None:
    state = ManualReviewState()
    state.request("pending", "review-4")
    assert state.is_rejected is False
    state.record_decision("rejected", "reviewer-b", "denied")
    assert state.is_rejected is True
    assert state.is_approved is False


def test_manual_review_state_snapshot_is_independent_copy() -> None:
    requested_at = datetime(2026, 3, 15, 8, 0, tzinfo=timezone.utc)
    state = ManualReviewState()
    state.request("check", "review-5", requested_at=requested_at)
    snap = state.snapshot()
    # Mutating original after snapshot must not affect snapshot.
    state.record_decision("approved", "reviewer-c")
    assert snap.is_pending is True
    assert snap.decision is None


# ---------------------------------------------------------------------------
# CompensationLog — additional paths
# ---------------------------------------------------------------------------


def test_compensation_log_from_snapshot_none_returns_empty_log() -> None:
    log = CompensationLog.from_snapshot(None)
    assert log.pending() == []


def test_compensation_log_mark_compensated_with_none_completed_at_stays_pending() -> None:
    # mark_compensated with completed_at=None leaves completed_at as None,
    # so the marker still appears in pending() — callers must supply a real
    # timestamp to actually retire an entry.
    log = CompensationLog()
    log.record("action-a", "res-a")
    log.mark_compensated("action-a", "res-a", completed_at=None)
    pending = log.pending()
    assert len(pending) == 1
    assert pending[0].resource_id == "res-a"
    assert pending[0].completed_at is None


def test_compensation_log_pending_returns_in_reverse_order() -> None:
    log = CompensationLog()
    log.record("first", "res-1")
    log.record("second", "res-2")
    log.record("third", "res-3")
    pending = log.pending()
    # pending() reverses: last recorded should appear first.
    assert [e.action for e in pending] == ["third", "second", "first"]


def test_compensation_log_snapshot_entries_are_independent_copies() -> None:
    log = CompensationLog()
    log.record("action-b", "res-b")
    snap = log.snapshot()
    # Mutating the original entry after snapshot must not corrupt the snapshot.
    log._entries[0].completed_at = datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc)
    assert snap[0].completed_at is None


# ---------------------------------------------------------------------------
# build_search_attribute_updates
# ---------------------------------------------------------------------------


def test_build_search_attribute_updates_empty_mapping_returns_empty_list() -> None:
    updates = build_search_attribute_updates({})
    assert updates == []


def test_build_search_attribute_updates_none_value_produces_unset_update() -> None:
    updates = build_search_attribute_updates({TENANT_ID: None})
    assert len(updates) == 1
    # An unset update carries no value — verify it is accepted without error.
    # The exact type is internal to the SDK; we only assert count and presence.


def test_build_search_attribute_updates_non_none_value_produces_set_update() -> None:
    updates = build_search_attribute_updates({STATUS: "running"})
    assert len(updates) == 1


def test_build_search_attribute_updates_mixed_none_and_value() -> None:
    updates = build_search_attribute_updates({TENANT_ID: "tenant-a", STATUS: None})
    assert len(updates) == 2


def test_build_search_attribute_updates_all_known_sa_keys_accepted() -> None:
    from dataspace_control_plane_procedures._shared.search_attributes import (
        AGREEMENT_ID,
        ASSET_ID,
        LEGAL_ENTITY_ID,
        PACK_ID,
        PROCEDURE_TYPE,
    )
    updates = build_search_attribute_updates(
        {
            TENANT_ID: "tenant-x",
            LEGAL_ENTITY_ID: "legal-x",
            PROCEDURE_TYPE: "onboarding",
            AGREEMENT_ID: "agr-1",
            ASSET_ID: "asset-1",
            STATUS: "completed",
            PACK_ID: "pack-1",
            EXTERNAL_REFERENCE: None,
        }
    )
    assert len(updates) == 8
