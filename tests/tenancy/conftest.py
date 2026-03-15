"""
tests/tenancy/conftest.py
Tenancy suite: proves cross-tenant isolation at the database, API, workflow, and search layers.

Requires: PostgreSQL with RLS policies enabled, application roles, seed data.
All tests require --live-services. Run-as-superuser tests are explicitly labeled.
"""
from __future__ import annotations

try:
    from tests.fixtures.containers import (  # noqa: F401
        postgres_container,
        keycloak_container,
        vault_container,
        kafka_container,
        toxiproxy_container,
    )
except Exception:
    pass

try:
    from tests.fixtures.postgres import (  # noqa: F401
        postgres_url,
        postgres_engine,
        postgres_superuser_conn,
        postgres_tenant_conn,
        create_rls_test_table,
    )
except Exception:
    pass

try:
    from tests.fixtures.temporal_env import (  # noqa: F401
        temporal_env,
        temporal_client,
        temporal_worker,
    )
except Exception:
    pass

from tests.fixtures.apps import (  # noqa: F401
    app_factory,
    test_app,
    test_client,
    async_client,
)
