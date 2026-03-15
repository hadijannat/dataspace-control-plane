from pydantic import BaseModel, Field


class PublicStartProcedureRequest(BaseModel):
    procedure_type: str = Field(..., description="Canonical procedure slug, e.g. company-onboarding")
    tenant_id: str
    legal_entity_id: str | None = None
    payload: dict = Field(default_factory=dict)
    idempotency_key: str | None = None

