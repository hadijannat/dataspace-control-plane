"""Test scenario catalogue for dpp_provision.

Each attribute names a scenario that must be covered by
``tests/unit/``, ``tests/integration/``, or ``tests/chaos/`` suites.
The strings are stable identifiers — rename only with a search-replace
across the test directory.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DppScenarios:
    happy_path: str = "happy_path"
    missing_mandatory_fields_triggers_review: str = "missing_mandatory_fields_triggers_review"
    low_completeness_score_blocks: str = "low_completeness_score_blocks"
    id_link_binding_retry: str = "id_link_binding_retry"
    source_snapshot_timeout: str = "source_snapshot_timeout"
    compensation_on_error: str = "compensation_on_error"


SCENARIOS = DppScenarios()
