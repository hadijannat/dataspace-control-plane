"""OIDC token validation backed by the shared Keycloak adapter."""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

import structlog
from dataspace_control_plane_adapters.infrastructure.keycloak.api import (
    JwksCache,
    KeycloakJwksRefreshError,
    KeycloakSettings,
    KeycloakTokenExpiredError,
    KeycloakTokenInvalidError,
    OidcVerifier,
)
from pydantic import SecretStr

from app.auth.principals import Principal
from app.settings import settings

logger = structlog.get_logger(__name__)


def _issuer_parts() -> tuple[str, str]:
    issuer = str(settings.oidc_issuer).rstrip("/")
    parsed = urlparse(issuer)
    marker = "/realms/"
    if marker not in parsed.path:
        raise RuntimeError(f"Unsupported OIDC issuer format: {issuer}")
    base_path, realm = parsed.path.rsplit(marker, 1)
    base_url = f"{parsed.scheme}://{parsed.netloc}{base_path}".rstrip("/")
    return base_url, realm


@lru_cache(maxsize=1)
def _verifier() -> OidcVerifier:
    base_url, realm = _issuer_parts()
    keycloak_settings = KeycloakSettings.model_construct(
        base_url=base_url,
        realm=realm,
        client_id=settings.oidc_audience,
        client_secret=SecretStr(""),
        jwks_cache_ttl_s=settings.oidc_jwks_cache_ttl,
        admin_client_id="admin-cli",
    )
    return OidcVerifier(keycloak_settings, JwksCache(keycloak_settings))


async def validate_token(token: str) -> Principal:
    """Validate a bearer JWT and return a Principal."""
    from fastapi import HTTPException, status

    try:
        claims = await _verifier().verify(token)
    except KeycloakTokenExpiredError as exc:
        logger.warning("auth.token_expired", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except (KeycloakTokenInvalidError, KeycloakJwksRefreshError) as exc:
        logger.warning("auth.token_invalid", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    realm_roles = frozenset(claims.get("realm_access", {}).get("roles", []))
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
