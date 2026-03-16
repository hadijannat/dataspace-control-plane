from pydantic import BaseModel


class StreamTicketRequest(BaseModel):
    workflow_id: str


class StreamTicketResponse(BaseModel):
    ticket: str
    expires_in_seconds: int
