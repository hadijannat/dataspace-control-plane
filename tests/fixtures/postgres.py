"""
PostgreSQL bootstrap fixtures: roles, schemas, RLS policies, seed data.
Depends on postgres_container from fixtures/containers.py.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Connection URL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def postgres_url(postgres_container) -> str:
    """Return psycopg2-compatible connection URL from the running postgres_container."""
    # get_connection_url() may include SQLAlchemy dialect prefix — strip it for psycopg2
    return postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")


# ---------------------------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_engine(postgres_container):
    """
    Session-scoped SQLAlchemy engine.

    Skipped if sqlalchemy is not installed.
    """
    sqlalchemy = pytest.importorskip("sqlalchemy", reason="sqlalchemy required for postgres_engine")
    url = postgres_container.get_connection_url()
    engine = sqlalchemy.create_engine(url)
    yield engine
    engine.dispose()


# ---------------------------------------------------------------------------
# Superuser psycopg2 connection
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def postgres_superuser_conn(postgres_container):
    """
    Function-scoped psycopg2 connection as superuser with autocommit=True.

    Skipped if psycopg2 is not installed.
    """
    psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for postgres_superuser_conn")
    url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Tenant role connection
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def postgres_tenant_conn(postgres_container, request: pytest.FixtureRequest):
    """
    Function-scoped psycopg2 connection scoped to an ephemeral tenant role.

    Creates role tenant_<nodeid_prefix>, returns a connection as that role.
    Drops the role on teardown.
    """
    psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for postgres_tenant_conn")
    postgres_url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")

    safe_id = request.node.nodeid[:8].replace("/", "_").replace(":", "_").replace(".", "_")
    role_name = f"tenant_{safe_id}"

    # Superuser connection to create the role
    admin_conn = psycopg2.connect(postgres_url)
    admin_conn.autocommit = True
    admin_cur = admin_conn.cursor()
    admin_cur.execute(f"CREATE ROLE {role_name} LOGIN PASSWORD 'tenantpass' NOSUPERUSER NOCREATEDB NOCREATEROLE")
    admin_cur.execute(f"GRANT ALL ON ALL TABLES IN SCHEMA public TO {role_name}")
    admin_cur.close()
    admin_conn.close()

    # Connect as tenant role
    import urllib.parse

    parsed = urllib.parse.urlparse(postgres_url)
    tenant_url = parsed._replace(
        netloc=f"{role_name}:tenantpass@{parsed.hostname}:{parsed.port}"
    ).geturl()
    tenant_conn = psycopg2.connect(tenant_url)
    tenant_conn.autocommit = True

    yield tenant_conn

    tenant_conn.close()

    # Teardown: drop role
    cleanup_conn = psycopg2.connect(postgres_url)
    cleanup_conn.autocommit = True
    cleanup_cur = cleanup_conn.cursor()
    cleanup_cur.execute(f"DROP ROLE IF EXISTS {role_name}")
    cleanup_cur.close()
    cleanup_conn.close()


# ---------------------------------------------------------------------------
# RLS test table setup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def create_rls_test_table(postgres_container):
    """
    Session-scoped fixture that creates rls_test_items with RLS enabled.

    Table: id SERIAL PK, tenant_id TEXT NOT NULL, payload TEXT.
    Policy: tenant_isolation_policy — tenant_id = current_setting('app.tenant_id', true).
    """
    psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for create_rls_test_table")
    # get_connection_url() returns SQLAlchemy dialect URL; strip the dialect prefix for psycopg2
    url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS rls_test_items CASCADE")
    cur.execute(
        """
        CREATE TABLE rls_test_items (
            id        SERIAL PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            payload   TEXT
        )
        """
    )
    cur.execute("ALTER TABLE rls_test_items ENABLE ROW LEVEL SECURITY")
    cur.execute(
        """
        CREATE POLICY tenant_isolation_policy ON rls_test_items
        USING (tenant_id = current_setting('app.tenant_id', true))
        """
    )
    cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON rls_test_items TO PUBLIC")
    cur.execute("GRANT USAGE, SELECT ON SEQUENCE rls_test_items_id_seq TO PUBLIC")
    cur.close()

    yield

    # Teardown
    teardown_cur = conn.cursor()
    teardown_cur.execute("DROP TABLE IF EXISTS rls_test_items CASCADE")
    teardown_cur.close()
    conn.close()
