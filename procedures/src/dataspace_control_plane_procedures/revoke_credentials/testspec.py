from dataclasses import dataclass


@dataclass
class RevocationScenarios:
    happy_path_urgent: str = "happy_path_urgent"
    issuer_async_confirmation_via_signal: str = "issuer_async_confirmation_via_signal"
    no_dependent_procedures: str = "no_dependent_procedures"
    dependent_procedures_frozen: str = "dependent_procedures_frozen"
    binding_propagation_retry: str = "binding_propagation_retry"
    status_update_fails: str = "status_update_fails"


SCENARIOS = RevocationScenarios()
