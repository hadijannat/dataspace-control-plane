import base64
import json
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.auth.principals import Principal
from app.services.stream_tickets import mint_stream_ticket, principal_from_stream_ticket


def test_stream_ticket_round_trip_restores_principal_claims():
    principal = Principal(
        subject="operator-1",
        email="ops@example.com",
        realm_roles=frozenset({"dataspace-admin"}),
        client_roles=frozenset({"operator"}),
        tenant_ids=frozenset({"tenant-a", "tenant-b"}),
    )

    restored = principal_from_stream_ticket(mint_stream_ticket(principal))

    assert restored.subject == principal.subject
    assert restored.email == principal.email
    assert restored.realm_roles == principal.realm_roles
    assert restored.client_roles == principal.client_roles
    assert restored.tenant_ids == principal.tenant_ids


def test_invalid_stream_ticket_is_rejected():
    with pytest.raises(Exception):
        principal_from_stream_ticket("invalid.ticket")


def test_expired_stream_ticket_is_rejected():
    """A ticket minted in the past (exp already elapsed) must be rejected with 401."""
    principal = Principal(
        subject="operator-expired",
        email="expired@example.com",
        realm_roles=frozenset(),
        client_roles=frozenset(),
        tenant_ids=frozenset(),
    )

    # Mint the ticket at a point in the past so that exp is already in the past.
    past_time = 1_000_000  # a fixed Unix timestamp well in the past
    with patch("app.services.stream_tickets.time") as mock_time:
        mock_time.time.return_value = past_time
        ticket = mint_stream_ticket(principal)

    # Validate at real (current) time — ticket is expired.
    with pytest.raises(HTTPException) as exc_info:
        principal_from_stream_ticket(ticket)

    assert exc_info.value.status_code == 401
    assert "Expired" in exc_info.value.detail


def test_tampered_stream_ticket_payload_is_rejected():
    """Modifying the payload segment after signing must invalidate the ticket."""
    principal = Principal(
        subject="operator-legit",
        email="legit@example.com",
        realm_roles=frozenset(),
        client_roles=frozenset(),
        tenant_ids=frozenset(),
    )

    ticket = mint_stream_ticket(principal)
    payload_segment, signature_segment = ticket.split(".", 1)

    # Decode the payload, tamper with the subject, and re-encode.
    padding = "=" * (-len(payload_segment) % 4)
    payload = json.loads(base64.urlsafe_b64decode(f"{payload_segment}{padding}"))
    payload["sub"] = "attacker"
    tampered_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).decode().rstrip("=")

    tampered_ticket = f"{tampered_payload}.{signature_segment}"

    with pytest.raises(HTTPException) as exc_info:
        principal_from_stream_ticket(tampered_ticket)

    assert exc_info.value.status_code == 401
    assert "Invalid" in exc_info.value.detail

