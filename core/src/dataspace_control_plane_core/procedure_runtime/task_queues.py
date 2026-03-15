from .procedure_ids import ProcedureType

TASK_QUEUE_MAP: dict[ProcedureType, str] = {
    ProcedureType.COMPANY_ONBOARDING: "onboarding",
    ProcedureType.CONNECTOR_BOOTSTRAP: "onboarding",
    ProcedureType.MACHINE_CREDENTIAL_ROTATION: "machine-trust",
    ProcedureType.ASSET_TWIN_PUBLICATION: "twins-publication",
    ProcedureType.CONTRACT_NEGOTIATION: "contracts-negotiation",
    ProcedureType.COMPLIANCE_GAP_SCAN: "compliance",
    ProcedureType.STALE_NEGOTIATION_SWEEP: "maintenance",
}


def task_queue_for(procedure_type: ProcedureType) -> str:
    q = TASK_QUEUE_MAP.get(procedure_type)
    if q is None:
        raise ValueError(f"No task queue for procedure type: {procedure_type}")
    return q
