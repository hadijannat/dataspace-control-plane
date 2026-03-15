from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.oidc import validate_token
from app.auth.principals import Principal
from app.services.stream_tickets import principal_from_stream_ticket

_bearer = HTTPBearer(auto_error=True)
_optional_bearer = HTTPBearer(auto_error=False)


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Principal:
    return await validate_token(credentials.credentials)


async def get_stream_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
) -> Principal:
    if credentials:
        return await validate_token(credentials.credentials)

    ticket = request.query_params.get("ticket")
    if ticket:
        return principal_from_stream_ticket(ticket)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing stream authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise AssertionError("unreachable")
