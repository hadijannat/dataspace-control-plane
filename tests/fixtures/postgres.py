"""
PostgreSQL bootstrap fixtures: roles, schemas, RLS policies, and seed data.
Depends on postgres_container from fixtures/containers.py.
"""
from __future__ import annotations

import urllib.parse
import uuid
from typing import Any

import pytest


def _postgresql_url(url: str) -> str:
    return url.replace("postgresql+psycopg2://", "postgresql://")


def _set_app_context(conn, tenant_id: str | None = None, legal_entity_id: str | None = None) -> None:
    cur = conn.cursor()
    if tenant_id is not None:
        cur.execute("SELECT set_config('app.tenant_id', %s, false)", (tenant_id,))
    if legal_entity_id is not None:
        cur.execute("SELECT set_config('app.legal_entity', %s, false)", (legal_entity_id,))
    cur.close()


# ---------------------------------------------------------------------------
# Connection URLs
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def postgres_url(postgres_container) -> str:
    """Return a psycopg-compatible connection URL from the running postgres container."""
    return _postgresql_url(postgres_container.get_connection_url())


# ---------------------------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_engine(postgres_container):
    """Session-scoped SQLAlchemy engine."""
    sqlalchemy = pytest.importorskip("sqlalchemy", reason="sqlalchemy required for postgres_engine")
    engine = sqlalchemy.create_engine(postgres_container.get_connection_url())
    yield engine
    engine.dispose()


# ---------------------------------------------------------------------------
# Admin connection
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def postgres_superuser_conn(postgres_url: str):
    """
    Function-scoped administrative psycopg2 connection with autocommit enabled.
    """
    psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for postgres fixtures")
    conn = psycopg2.connect(postgres_url)
    conn.autocommit = True
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Role / connection factories
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def postgres_role_connection_factory(postgres_url: str):
    """
    Build ephemeral PostgreSQL roles and connections for RLS-oriented tests.

    Returns a callable that yields ``(conn, role_name)`` for the requested role shape.
    All roles and connections are cleaned up automatically.
    """
    psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for postgres fixtures")

    open_conns: list[Any] = []
    created_roles: list[str] = []

    def create(
        *,
        tenant_id: str | None = None,
        legal_entity_id: str | None = None,
        bypassrls: bool = False,
        superuser: bool = False,
        role_name: str | None = None,
        password: str = "tenantpass",
    ):
        safe_role_name = role_name or f"rls_{uuid.uuid4().hex[:10]}"

        admin_conn = psycopg2.connect(postgres_url)
        admin_conn.autocommit = True
        admin_cur = admin_conn.cursor()
        admin_cur.execute(
            f"""
            CREATE ROLE {safe_role_name}
            LOGIN
            PASSWORD %s
            {"SUPERUSER" if superuser else "NOSUPERUSER"}
            {"BYPASSRLS" if bypassrls else "NOBYPASSRLS"}
            NOCREATEDB
            NOCREATEROLE
            """,
            (password,),
        )
        admin_cur.close()
        admin_conn.close()

        parsed = urllib.parse.urlparse(postgres_url)
        conn = psycopg2.connect(
            dbname=parsed.path.lstrip("/"),
            host=parsed.hostname,
            port=parsed.port,
            user=safe_role_name,
            password=password,
        )
        conn.autocommit = True
        _set_app_context(conn, tenant_id=tenant_id, legal_entity_id=legal_entity_id)

        created_roles.append(safe_role_name)
        open_conns.append(conn)
        return conn, safe_role_name

    yield create

    for conn in reversed(open_conns):
        try:
            conn.close()
        except Exception:
            pass

    cleanup_conn = psycopg2.connect(postgres_url)
    cleanup_conn.autocommit = True
    cleanup_cur = cleanup_conn.cursor()
    for role_name in reversed(created_roles):
        cleanup_cur.execute(f"DROP ROLE IF EXISTS {role_name}")
    cleanup_cur.close()
    cleanup_conn.close()


@pytest.fixture(scope="function")
def postgres_tenant_conn(postgres_role_connection_factory):
    """Backwards-compatible single-tenant role connection used by a subset of tests."""
    conn, _role_name = postgres_role_connection_factory(tenant_id="tenant_default")
    return conn


# ---------------------------------------------------------------------------
# RLS table fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def create_rls_test_table(postgres_superuser_conn, postgres_role_connection_factory):
    """
    Create an RLS-protected tenant table owned by a non-superuser role.

    Policy: tenant_id must match current_setting('app.tenant_id', true).
    """
    owner_conn, owner_role = postgres_role_connection_factory(role_name=f"rls_owner_{uuid.uuid4().hex[:8]}")
    owner_cur = owner_conn.cursor()
    owner_cur.execute(
        """
        CREATE TABLE rls_test_items (
            id SERIAL PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            legal_entity_id TEXT NOT NULL DEFAULT '',
            payload TEXT
        )
        """
    )
    owner_cur.execute("ALTER TABLE rls_test_items ENABLE ROW LEVEL SECURITY")
    owner_cur.execute(
        """
        CREATE POLICY tenant_isolation_policy ON rls_test_items
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
        """
    )
    owner_cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON rls_test_items TO PUBLIC")
    owner_cur.execute("GRANT USAGE, SELECT ON SEQUENCE rls_test_items_id_seq TO PUBLIC")
    owner_cur.close()

    yield {"owner_conn": owner_conn, "owner_role": owner_role, "table_name": "rls_test_items"}

    teardown_cur = postgres_superuser_conn.cursor()
    teardown_cur.execute("DROP TABLE IF EXISTS rls_test_items CASCADE")
    teardown_cur.close()


@pytest.fixture(scope="function")
def create_legal_entity_test_table(postgres_superuser_conn, postgres_role_connection_factory):
    """
    Create an RLS-protected legal-entity table owned by a non-superuser role.

    Policy: tenant_id and legal_entity_id must match the session context.
    """
    owner_conn, owner_role = postgres_role_connection_factory(
        role_name=f"rls_legal_owner_{uuid.uuid4().hex[:8]}"
    )
    owner_cur = owner_conn.cursor()
    owner_cur.execute(
        """
        CREATE TABLE rls_legal_entity_test (
            id SERIAL PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            legal_entity_id TEXT NOT NULL,
            payload TEXT
        )
        """
    )
    owner_cur.execute("ALTER TABLE rls_legal_entity_test ENABLE ROW LEVEL SECURITY")
    owner_cur.execute(
        """
        CREATE POLICY legal_entity_isolation_policy ON rls_legal_entity_test
        USING (
            tenant_id = current_setting('app.tenant_id', true)
            AND legal_entity_id = current_setting('app.legal_entity', true)
        )
        WITH CHECK (
            tenant_id = current_setting('app.tenant_id', true)
            AND legal_entity_id = current_setting('app.legal_entity', true)
        )
        """
    )
    owner_cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON rls_legal_entity_test TO PUBLIC")
    owner_cur.execute("GRANT USAGE, SELECT ON SEQUENCE rls_legal_entity_test_id_seq TO PUBLIC")
    owner_cur.close()

    yield {
        "owner_conn": owner_conn,
        "owner_role": owner_role,
        "table_name": "rls_legal_entity_test",
    }

    teardown_cur = postgres_superuser_conn.cursor()
    teardown_cur.execute("DROP TABLE IF EXISTS rls_legal_entity_test CASCADE")
    teardown_cur.close()
