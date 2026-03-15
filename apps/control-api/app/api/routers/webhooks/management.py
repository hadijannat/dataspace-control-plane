from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.api.schemas.webhooks import WebhookAcceptedResponse
from app.services import audit
from app.settings import settings

router = APIRouter()


def _validate_signature(body: bytes, signature: str | None) -> None:
    if settings.webhook_shared_secret is None:
        return
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature",
        )
    expected = hmac.new(
        settings.webhook_shared_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )


@router.post(
    "/management",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=WebhookAcceptedResponse,
    operation_id="receive_management_webhook",
)
async def receive_management_webhook(
    request: Request,
    event_type: str = Header(default="unknown", alias="X-Dataspace-Event-Type"),
    signature: str | None = Header(default=None, alias="X-Dataspace-Signature"),
) -> WebhookAcceptedResponse:
    payload = await request.body()
    _validate_signature(payload, signature)

    correlation_id: str | None = getattr(request.state, "correlation_id", None)
    await audit.emit(
        event_type="webhook.received",
        actor_subject="external-webhook",
        tenant_id=None,
        resource_type="webhook",
        resource_id=event_type,
        metadata={"correlation_id": correlation_id},
    )

    return WebhookAcceptedResponse(correlation_id=correlation_id)

