from .procedure_ids import ProcedureType
from .workflow_contracts import ProcedureInput
from .errors import ProcedureInputValidationError

REQUIRED_PAYLOAD_KEYS: dict[ProcedureType, list[str]] = {
    ProcedureType.COMPANY_ONBOARDING: ["legal_entity_id", "bpnl"],
    ProcedureType.CONNECTOR_BOOTSTRAP: ["legal_entity_id", "connector_url"],
    ProcedureType.MACHINE_CREDENTIAL_ROTATION: ["legal_entity_id", "credential_type"],
    ProcedureType.ASSET_TWIN_PUBLICATION: ["legal_entity_id", "global_asset_id"],
    ProcedureType.CONTRACT_NEGOTIATION: ["legal_entity_id", "offer_id", "counterparty_connector"],
    ProcedureType.COMPLIANCE_GAP_SCAN: ["legal_entity_id"],
    ProcedureType.STALE_NEGOTIATION_SWEEP: [],
}


def validate_procedure_input(inp: ProcedureInput) -> None:
    required = REQUIRED_PAYLOAD_KEYS.get(inp.procedure_type, [])
    missing = [k for k in required if k not in inp.payload]
    if missing:
        raise ProcedureInputValidationError(
            f"Missing required payload keys for {inp.procedure_type}: {missing}"
        )
