"""
tests/chaos/conftest.py
Deterministic failure injection suite.

Uses Toxiproxy to inject latency, resets, and blackholes.
All chaos tests require --live-services and Docker.
Randomized combinations are nightly-only (@pytest.mark.nightly).
"""
from __future__ import annotations

try:
    from tests.fixtures.containers import (  # noqa: F401
        postgres_container,
        vault_container,
        kafka_container,
        toxiproxy_container,
    )
except Exception:
    pass

try:
    from tests.fixtures.toxiproxy import (  # noqa: F401
        toxiproxy_api_url,
        toxiproxy_proxy,
        add_latency_toxic,
        add_reset_peer_toxic,
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
    from tests.fixtures.postgres import (  # noqa: F401
        postgres_url,
        postgres_superuser_conn,
        create_rls_test_table,
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
