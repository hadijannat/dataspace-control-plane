from dataclasses import dataclass


@dataclass
class TwinRegistrationScenarios:
    happy_path: str = "happy_path"
    semantic_id_ambiguous_triggers_review: str = "semantic_id_ambiguous_triggers_review"
    submodel_upsert_retry: str = "submodel_upsert_retry"
    registry_not_found_retry: str = "registry_not_found_retry"
    access_binding_fails_compensates: str = "access_binding_fails_compensates"
    readback_verification_fails: str = "readback_verification_fails"


SCENARIOS = TwinRegistrationScenarios()
