"""Public import surface for the Keycloak infrastructure adapter.

Other adapters and apps import from here — never from internal sub-modules.

Quick-start::

    from dataspace_control_plane_adapters.infrastructure.keycloak.api import (
        KeycloakSettings,
        OidcVerifier,
        JwksCache,
        KeycloakAdminClient,
        KeycloakAuthorizationPort,
        KeycloakHealthProbe,
        claims_to_principal,
    )

    settings = KeycloakSettings()
    cache = JwksCache(settings)
    verifier = OidcVerifier(settings, cache)

    claims = await verifier.verify(bearer_token)
    principal = claims_to_principal(claims, client_id=settings.client_id)

    authz = KeycloakAuthorizationPort()
    decision = authz.decide(principal, "write", scope)
"""
from __future__ import annotations

from dataspace_control_plane_adapters.infrastructure.keycloak.config import (
    KeycloakSettings,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.jwks_cache import (
    JwksCache,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.oidc_verifier import (
    OidcVerifier,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.admin_client import (
    KeycloakAdminClient,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.role_mapper import (
    KEYCLOAK_ROLE_MAP,
    map_roles,
    map_role,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.principal_mapper import (
    claims_to_principal,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.ports_impl import (
    KeycloakAuthorizationPort,
    ROLE_ACTION_MATRIX,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.health import (
    KeycloakHealthProbe,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.errors import (
    KeycloakError,
    KeycloakTokenExpiredError,
    KeycloakTokenInvalidError,
    KeycloakJwksRefreshError,
    KeycloakAdminError,
)

__all__ = [
    # Configuration
    "KeycloakSettings",
    # JWKS
    "JwksCache",
    # Token verification
    "OidcVerifier",
    # Admin REST API
    "KeycloakAdminClient",
    # Role mapping
    "KEYCLOAK_ROLE_MAP",
    "map_roles",
    "map_role",
    # Principal mapping
    "claims_to_principal",
    # Authorization port
    "KeycloakAuthorizationPort",
    "ROLE_ACTION_MATRIX",
    # Health
    "KeycloakHealthProbe",
    # Errors
    "KeycloakError",
    "KeycloakTokenExpiredError",
    "KeycloakTokenInvalidError",
    "KeycloakJwksRefreshError",
    "KeycloakAdminError",
]
