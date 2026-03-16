from __future__ import annotations

import base64
import json
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.auth.principals import Principal
from app.services.stream_tickets import mint_stream_ticket, principal_from_stream_ticket


def _principal() -> Principal:
    return Principal(
        subject="operator-1",
        email="ops@example.com",
        realm_roles=frozenset({"dataspace-admin"}),
        client_roles=frozenset({"operator"}),
        tenant_ids=frozenset({"tenant-a", "tenant-b"}),
    )


def test_stream_ticket_round_trip_restores_principal_claims() -> None:
    restored = principal_from_stream_ticket(
        mint_stream_ticket(_principal(), workflow_id="wf-1", tenant_id="tenant-a"),
        workflow_id="wf-1",
    )

    assert restored.subject == "operator-1"
    assert restored.email == "ops@example.com"
    assert restored.tenant_ids == frozenset({"tenant-a", "tenant-b"})


def test_stream_ticket_rejects_wrong_workflow() -> None:
    ticket = mint_stream_ticket(_principal(), workflow_id="wf-1", tenant_id="tenant-a")

    with pytest.raises(HTTPException) as exc_info:
        principal_from_stream_ticket(ticket, workflow_id="wf-2")

    assert exc_info.value.status_code == 401
    assert "not valid for this workflow" in exc_info.value.detail


def test_expired_stream_ticket_is_rejected() -> None:
    past_time = 1_000_000
    with patch("app.services.stream_tickets.time") as mock_time:
        mock_time.time.return_value = past_time
        ticket = mint_stream_ticket(_principal(), workflow_id="wf-1", tenant_id="tenant-a")

    with pytest.raises(HTTPException) as exc_info:
        principal_from_stream_ticket(ticket, workflow_id="wf-1")

    assert exc_info.value.status_code == 401
    assert "Expired" in exc_info.value.detail


def test_tampered_stream_ticket_payload_is_rejected() -> None:
    ticket = mint_stream_ticket(_principal(), workflow_id="wf-1", tenant_id="tenant-a")
    payload_segment, signature_segment = ticket.split(".", 1)

    padding = "=" * (-len(payload_segment) % 4)
    payload = json.loads(base64.urlsafe_b64decode(f"{payload_segment}{padding}"))
    payload["workflow_id"] = "wf-2"
    tampered_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).decode().rstrip("=")
    tampered_ticket = f"{tampered_payload}.{signature_segment}"

    with pytest.raises(HTTPException) as exc_info:
        principal_from_stream_ticket(tampered_ticket, workflow_id="wf-2")

    assert exc_info.value.status_code == 401
    assert "Invalid" in exc_info.value.detail


def test_invalid_stream_ticket_is_rejected() -> None:
    with pytest.raises(HTTPException):
        principal_from_stream_ticket("invalid.ticket", workflow_id="wf-1")
