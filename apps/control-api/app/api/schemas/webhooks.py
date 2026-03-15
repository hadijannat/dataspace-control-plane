from pydantic import BaseModel


class WebhookAcceptedResponse(BaseModel):
    accepted: bool = True
    correlation_id: str | None = None

