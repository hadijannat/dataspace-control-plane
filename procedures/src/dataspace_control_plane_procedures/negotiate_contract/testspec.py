"""Test scenario catalogue for negotiate_contract.

Each attribute names a scenario that must be covered by
``tests/unit/``, ``tests/integration/``, or ``tests/chaos/`` suites.
The strings are stable identifiers — rename only with a search-replace
across the test directory.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class NegotiationScenarios:
    happy_path_direct_accept: str = "happy_path_direct_accept"
    counterparty_sends_counteroffer_accepted_by_update: str = "counterparty_sends_counteroffer_accepted_by_update"
    counterparty_rejects: str = "counterparty_rejects"
    negotiation_expires: str = "negotiation_expires"
    credential_check_fails: str = "credential_check_fails"
    duplicate_accepted_signal_deduplicated: str = "duplicate_accepted_signal_deduplicated"
    continue_as_new_on_long_negotiation: str = "continue_as_new_on_long_negotiation"


SCENARIOS = NegotiationScenarios()
