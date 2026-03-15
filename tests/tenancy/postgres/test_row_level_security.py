"""
Verifies PostgreSQL Row-Level Security policies enforce tenant and legal-entity isolation.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.tenancy


def _set_context(conn, tenant_id: str | None = None, legal_entity_id: str | None = None) -> None:
    cur = conn.cursor()
    if tenant_id is not None:
        cur.execute("SELECT set_config('app.tenant_id', %s, false)", (tenant_id,))
    if legal_entity_id is not None:
        cur.execute("SELECT set_config('app.legal_entity', %s, false)", (legal_entity_id,))
    cur.close()


def _insert_tenant_row(conn, tenant_id: str, payload: str, legal_entity_id: str = "") -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO rls_test_items (tenant_id, legal_entity_id, payload)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (tenant_id, legal_entity_id, payload),
    )
    row_id = cur.fetchone()[0]
    cur.close()
    return row_id


def test_tenant_a_cannot_read_tenant_b_rows(
    create_rls_test_table, postgres_superuser_conn, postgres_role_connection_factory
) -> None:
    _insert_tenant_row(postgres_superuser_conn, "tenant_A", "payload_for_A")
    _insert_tenant_row(postgres_superuser_conn, "tenant_B", "payload_for_B")

    tenant_a_conn, _role_name = postgres_role_connection_factory(tenant_id="tenant_A")
    cur = tenant_a_conn.cursor()
    cur.execute("SELECT tenant_id FROM rls_test_items ORDER BY tenant_id")
    visible_tenants = [row[0] for row in cur.fetchall()]
    cur.close()

    assert visible_tenants == ["tenant_A"]


def test_tenant_a_cannot_mutate_tenant_b_rows(
    create_rls_test_table, postgres_superuser_conn, postgres_role_connection_factory
) -> None:
    row_id = _insert_tenant_row(postgres_superuser_conn, "tenant_B", "b-payload")

    tenant_a_conn, _role_name = postgres_role_connection_factory(tenant_id="tenant_A")
    cur = tenant_a_conn.cursor()
    cur.execute(
        "UPDATE rls_test_items SET payload = %s WHERE id = %s",
        ("mutated-by-tenant-a", row_id),
    )
    updated_rows = cur.rowcount
    cur.close()

    verify_cur = postgres_superuser_conn.cursor()
    verify_cur.execute("SELECT payload FROM rls_test_items WHERE id = %s", (row_id,))
    payload = verify_cur.fetchone()[0]
    verify_cur.close()

    assert updated_rows == 0
    assert payload == "b-payload"


def test_superuser_bypasses_rls(create_rls_test_table, postgres_superuser_conn) -> None:
    _insert_tenant_row(postgres_superuser_conn, "tenant_X", "x-payload")
    _insert_tenant_row(postgres_superuser_conn, "tenant_Y", "y-payload")

    cur = postgres_superuser_conn.cursor()
    cur.execute("SELECT DISTINCT tenant_id FROM rls_test_items ORDER BY tenant_id")
    tenants = [row[0] for row in cur.fetchall()]
    cur.close()

    assert tenants == ["tenant_X", "tenant_Y"]


def test_bypassrls_role_bypasses_rls(
    create_rls_test_table, postgres_superuser_conn, postgres_role_connection_factory
) -> None:
    _insert_tenant_row(postgres_superuser_conn, "tenant_bypass_A", "a-payload")
    _insert_tenant_row(postgres_superuser_conn, "tenant_bypass_B", "b-payload")

    bypass_conn, _role_name = postgres_role_connection_factory(bypassrls=True)
    cur = bypass_conn.cursor()
    cur.execute("SELECT DISTINCT tenant_id FROM rls_test_items ORDER BY tenant_id")
    tenants = [row[0] for row in cur.fetchall()]
    cur.close()

    assert tenants == ["tenant_bypass_A", "tenant_bypass_B"]


def test_table_owner_subject_to_rls_when_forced(
    create_rls_test_table, postgres_superuser_conn
) -> None:
    owner_conn = create_rls_test_table["owner_conn"]
    _insert_tenant_row(postgres_superuser_conn, "tenant_A", "payload_for_A")
    _insert_tenant_row(postgres_superuser_conn, "tenant_B", "payload_for_B")

    force_cur = postgres_superuser_conn.cursor()
    force_cur.execute("ALTER TABLE rls_test_items FORCE ROW LEVEL SECURITY")
    force_cur.close()

    _set_context(owner_conn, tenant_id="tenant_A")
    owner_cur = owner_conn.cursor()
    owner_cur.execute("SELECT tenant_id FROM rls_test_items ORDER BY tenant_id")
    visible_tenants = [row[0] for row in owner_cur.fetchall()]
    owner_cur.close()

    restore_cur = postgres_superuser_conn.cursor()
    restore_cur.execute("ALTER TABLE rls_test_items NO FORCE ROW LEVEL SECURITY")
    restore_cur.close()

    assert visible_tenants == ["tenant_A"]


def test_legal_entity_isolation_within_tenant(
    create_legal_entity_test_table, postgres_superuser_conn, postgres_role_connection_factory
) -> None:
    cur = postgres_superuser_conn.cursor()
    cur.execute(
        """
        INSERT INTO rls_legal_entity_test (tenant_id, legal_entity_id, payload)
        VALUES
            ('tenant_1', 'entity_A', 'payload_A'),
            ('tenant_1', 'entity_B', 'payload_B')
        """
    )
    cur.close()

    entity_a_conn, _role_name = postgres_role_connection_factory(
        tenant_id="tenant_1",
        legal_entity_id="entity_A",
    )
    entity_cur = entity_a_conn.cursor()
    entity_cur.execute(
        "SELECT legal_entity_id FROM rls_legal_entity_test ORDER BY legal_entity_id"
    )
    visible_entities = [row[0] for row in entity_cur.fetchall()]
    entity_cur.close()

    assert visible_entities == ["entity_A"]
