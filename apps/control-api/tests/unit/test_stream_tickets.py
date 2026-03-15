import pytest

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

