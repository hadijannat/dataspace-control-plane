"""Test scenario catalogue for company_onboarding.

Each attribute names a scenario that must be covered by
``tests/unit/``, ``tests/integration/``, or ``tests/chaos/`` suites.
The strings are stable identifiers — rename only with a search-replace
across the test directory.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OnboardingScenarios:
    happy_path_catena_x: str = "happy_path_catena_x"
    approval_rejected_then_resubmit: str = "approval_rejected_then_resubmit"
    connector_bootstrap_fails_with_compensation: str = "connector_bootstrap_fails_with_compensation"
    continue_as_new_after_long_approval_wait: str = "continue_as_new_after_long_approval_wait"
    duplicate_external_approval_callback_deduplicated: str = "duplicate_external_approval_callback_deduplicated"
    manual_review_rejected_via_update: str = "manual_review_rejected_via_update"


SCENARIOS = OnboardingScenarios()
