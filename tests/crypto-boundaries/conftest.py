"""
tests/crypto-boundaries/conftest.py
Proves the platform's trust model and key custody boundaries.

Invariants:
- No raw private key material is persisted in Postgres.
- No operator-facing API returns PEM/key bytes.
- Only key references or aliases flow through domain and procedure state.
- Revocation and rotation paths work when old key refs exist in historical records.

Requires: Vault container (vault_container fixture), --live-services flag.
"""
from __future__ import annotations

try:
    from tests.fixtures.containers import (  # noqa: F401
        postgres_container,
        vault_container,
        keycloak_container,
        kafka_container,
        toxiproxy_container,
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
    from tests.fixtures.postgres import (  # noqa: F401
        postgres_url,
        postgres_superuser_conn,
        create_rls_test_table,
    )
except Exception:
    pass

from tests.fixtures.apps import (  # noqa: F401
    app_factory,
    test_app,
    test_client,
    async_client,
)
