"""Test scenario catalogue for connector_bootstrap.

Each attribute names a scenario that must be covered by
``tests/unit/``, ``tests/integration/``, or ``tests/chaos/`` suites.
The strings are stable identifiers — rename only with a search-replace
across the test directory.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorBootstrapScenarios:
    happy_path: str = "happy_path"
    infra_apply_fails_and_compensates: str = "infra_apply_fails_and_compensates"
    runtime_health_check_retries: str = "runtime_health_check_retries"
    wallet_link_signal_received: str = "wallet_link_signal_received"
    discovery_not_found_retried: str = "discovery_not_found_retried"
    degraded_signal_received: str = "degraded_signal_received"


SCENARIOS = ConnectorBootstrapScenarios()
