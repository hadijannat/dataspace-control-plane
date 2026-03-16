from __future__ import annotations

import json

import pytest

from app.application.dto.procedures import ProcedureStatusDTO
from app.services.workflow_streams import iter_workflow_status_events


@pytest.mark.asyncio
async def test_sse_emits_when_only_phase_changes(monkeypatch) -> None:
    snapshots = iter(
        [
            ProcedureStatusDTO(
                workflow_id="wf-1",
                procedure_type="company-onboarding",
                tenant_id="tenant-a",
                status="running",
                phase="awaiting_approval",
                progress_percent=40,
                search_attributes={},
                started_at="2024-01-01T00:00:00+00:00",
                updated_at="2024-01-01T00:00:01+00:00",
            ),
            ProcedureStatusDTO(
                workflow_id="wf-1",
                procedure_type="company-onboarding",
                tenant_id="tenant-a",
                status="running",
                phase="trust_bootstrap_completed",
                progress_percent=70,
                search_attributes={},
                started_at="2024-01-01T00:00:00+00:00",
                updated_at="2024-01-01T00:00:02+00:00",
            ),
            ProcedureStatusDTO(
                workflow_id="wf-1",
                procedure_type="company-onboarding",
                tenant_id="tenant-a",
                status="completed",
                phase="completed",
                progress_percent=100,
                search_attributes={},
                started_at="2024-01-01T00:00:00+00:00",
                updated_at="2024-01-01T00:00:03+00:00",
            ),
        ]
    )

    async def _fake_load_status(*args, **kwargs):
        return next(snapshots)

    async def _never_stop() -> bool:
        return False

    monkeypatch.setattr("app.services.workflow_streams.load_procedure_status", _fake_load_status)
    monkeypatch.setattr("app.services.workflow_streams.settings.stream_poll_interval_seconds", 0)

    events = []
    async for event in iter_workflow_status_events(
        "wf-1",
        catalog=None,
        gateway=None,
        pool=None,
        should_stop=_never_stop,
    ):
        events.append(json.loads(event))
        if len(events) == 3:
            break

    assert [event["phase"] for event in events] == [
        "awaiting_approval",
        "trust_bootstrap_completed",
        "completed",
    ]
