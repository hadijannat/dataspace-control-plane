from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import HTTPException, status

from app.auth.principals import Principal
from app.settings import settings


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _require_secret() -> str:
    if not settings.stream_ticket_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stream tickets are not configured",
        )
    return settings.stream_ticket_secret


def _payload_for(
    principal: Principal,
    *,
    workflow_id: str,
    tenant_id: str,
) -> dict[str, Any]:
    return {
        "aud": "procedure-stream",
        "sub": principal.subject,
        "email": principal.email,
        "realm_roles": sorted(principal.realm_roles),
        "client_roles": sorted(principal.client_roles),
        "tenant_ids": sorted(principal.tenant_ids),
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "exp": int(time.time()) + settings.stream_ticket_ttl_seconds,
    }


def mint_stream_ticket(
    principal: Principal,
    *,
    workflow_id: str,
    tenant_id: str,
) -> str:
    secret = _require_secret()
    payload = json.dumps(
        _payload_for(principal, workflow_id=workflow_id, tenant_id=tenant_id),
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    payload_segment = _b64encode(payload)
    signature = hmac.new(
        secret.encode(),
        payload_segment.encode(),
        hashlib.sha256,
    ).digest()
    return f"{payload_segment}.{_b64encode(signature)}"


def principal_from_stream_ticket(ticket: str, *, workflow_id: str) -> Principal:
    secret = _require_secret()
    try:
        payload_segment, signature_segment = ticket.split(".", 1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed stream ticket",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    expected_signature = _b64encode(
        hmac.new(
            secret.encode(),
            payload_segment.encode(),
            hashlib.sha256,
        ).digest()
    )
    if not hmac.compare_digest(signature_segment, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid stream ticket",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = json.loads(_b64decode(payload_segment))
    if payload.get("aud") != "procedure-stream":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid stream ticket audience",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if int(payload["exp"]) < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired stream ticket",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("workflow_id") != workflow_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Stream ticket is not valid for this workflow",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Principal(
        subject=payload["sub"],
        email=payload.get("email"),
        realm_roles=frozenset(payload.get("realm_roles", [])),
        client_roles=frozenset(payload.get("client_roles", [])),
        tenant_ids=frozenset(payload.get("tenant_ids", [])),
    )
