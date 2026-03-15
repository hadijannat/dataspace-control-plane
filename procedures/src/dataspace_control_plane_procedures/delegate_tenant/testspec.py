"""Test scenario catalogue for delegate_tenant.

Each attribute names a scenario that must be covered by
``tests/unit/``, ``tests/integration/``, or ``tests/chaos/`` suites.
The strings are stable identifiers — rename only with a search-replace
across the test directory.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DelegationScenarios:
    happy_path_shared_connector: str = "happy_path_shared_connector"
    happy_path_dedicated_connector: str = "happy_path_dedicated_connector"
    cross_border_requires_manual_review: str = "cross_border_requires_manual_review"
    auto_mode_decides_dedicated: str = "auto_mode_decides_dedicated"
    identity_isolation_verification_fails: str = "identity_isolation_verification_fails"
    compensation_on_failure: str = "compensation_on_failure"


SCENARIOS = DelegationScenarios()
