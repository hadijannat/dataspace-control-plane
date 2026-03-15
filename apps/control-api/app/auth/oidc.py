"""
OIDC token validation via cached JWKS.
Validates bearer tokens issued by Keycloak; extracts principal.
"""
import time
from typing import Any

import httpx
import structlog
from jose import JWTError, jwt

from app.settings import settings
from app.auth.principals import Principal

logger = structlog.get_logger(__name__)

_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0.0


async def _get_jwks() -> dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if now - _jwks_fetched_at < settings.oidc_jwks_cache_ttl and _jwks_cache:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.oidc_issuer}/.well-known/openid-configuration")
        resp.raise_for_status()
        jwks_uri = resp.json()["jwks_uri"]
        jwks_resp = await client.get(jwks_uri)
        jwks_resp.raise_for_status()
        _jwks_cache = jwks_resp.json()
        _jwks_fetched_at = now
    return _jwks_cache


async def validate_token(token: str) -> Principal:
    """Validate a bearer JWT and return a Principal. Raises HTTPException on failure."""
    from fastapi import HTTPException, status

    try:
        jwks = await _get_jwks()
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=str(settings.oidc_issuer),
        )
    except JWTError as exc:
        logger.warning("auth.token_invalid", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    realm_roles = frozenset(
        claims.get("realm_access", {}).get("roles", [])
    )
    client_roles = frozenset(
        claims.get("resource_access", {}).get(settings.oidc_audience, {}).get("roles", [])
    )
    tenant_ids = frozenset(claims.get("tenant_ids", []))

    return Principal(
        subject=claims["sub"],
        email=claims.get("email"),
        realm_roles=realm_roles,
        client_roles=client_roles,
        tenant_ids=tenant_ids,
    )
