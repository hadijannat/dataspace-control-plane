"""
tests/integration/conftest.py
Shared fixtures for integration test suite.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Re-export fixtures from fixture modules, handling missing optional deps
# ---------------------------------------------------------------------------

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
    from tests.fixtures.vault import (  # noqa: F401
        vault_client,
        vault_transit_key,
        vault_pki_role,
    )
except Exception:
    pass

try:
    from tests.fixtures.keycloak import (  # noqa: F401
        keycloak_admin_url,
        keycloak_realm,
        keycloak_client,
        keycloak_operator_user,
    )
except Exception:
    pass

try:
    from tests.fixtures.kafka import (  # noqa: F401
        kafka_bootstrap,
        kafka_producer,
        kafka_consumer,
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

from tests.fixtures.pack_profiles import (  # noqa: F401
    catenax_pack_profile,
    battery_passport_pack_profile,
    all_pack_profiles,
)
