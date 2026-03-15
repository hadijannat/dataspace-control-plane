"""Maps decoded OIDC claims to core ``OperatorPrincipal`` snapshots.

The ``OperatorPrincipal`` is a frozen dataclass defined in
``core/domains/operator_access/model/aggregates.py``.  It represents the
normalized identity of an authenticated human operator.

Claim extraction strategy
--------------------------
- ``sub``                 → ``OperatorPrincipal.subject``
- ``email``               → ``OperatorPrincipal.email`` (optional in claims)
- ``realm_access.roles``  → mapped via ``role_mapper.map_roles``
                            → ``OperatorPrincipal.realm_roles``
- ``resource_access.{client}.roles`` → ``OperatorPrincipal.client_roles``
- ``tenant`` / ``tenants`` / ``tenant_ids`` claims → ``OperatorPrincipal.tenant_ids``
  (Keycloak can be configured to embed a custom ``tenant`` claim via a mapper)

Design decisions
----------------
- This function is intentionally pure (no async, no I/O).
- Token strings are never included in the return value.
- If a claim is absent, sensible empty defaults are used rather than raising.
"""
from __future__ import annotations

from typing import Any

from dataspace_control_plane_adapters.infrastructure.keycloak.role_mapper import map_roles


def claims_to_principal(claims: dict, client_id: str = "") -> Any:  # OperatorPrincipal
    """Convert decoded OIDC JWT claims to a core ``OperatorPrincipal``.

    Parameters
    ----------
    claims:
        Decoded JWT payload dict (as returned by ``OidcVerifier.verify``).
    client_id:
        Optional: the OIDC client_id used to extract client-specific roles
        from ``resource_access``.  If empty, client_roles is empty.

    Returns
    -------
    OperatorPrincipal
        Frozen snapshot of the operator's identity.  Never contains raw tokens
        or Keycloak-internal credentials.
    """
    # Lazy import — keeps adapter startup cheap and avoids pulling core into
    # module-level scope unnecessarily.
    from dataspace_control_plane_core.domains.operator_access.model.aggregates import (  # noqa: PLC0415
        OperatorPrincipal,
    )

    subject: str = claims.get("sub", "")
    email: str | None = claims.get("email") or None

    # Realm-level roles (standard Keycloak claim).
    raw_realm_roles: list[str] = (
        claims.get("realm_access", {}).get("roles", [])
    )
    mapped_realm_roles: list[str] = map_roles(raw_realm_roles)

    # Client-specific roles.
    raw_client_roles: list[str] = []
    if client_id:
        raw_client_roles = (
            claims.get("resource_access", {})
            .get(client_id, {})
            .get("roles", [])
        )
    mapped_client_roles: list[str] = map_roles(raw_client_roles)

    # Tenant IDs — extracted from custom Keycloak claims.
    # Supports three possible claim names for flexibility across realm configs.
    tenant_ids: list[str] = []
    if "tenant_ids" in claims:
        raw = claims["tenant_ids"]
        tenant_ids = raw if isinstance(raw, list) else [str(raw)]
    elif "tenants" in claims:
        raw = claims["tenants"]
        tenant_ids = raw if isinstance(raw, list) else [str(raw)]
    elif "tenant" in claims:
        raw = claims["tenant"]
        tenant_ids = [str(raw)] if raw else []

    return OperatorPrincipal(
        subject=subject,
        email=email,
        realm_roles=frozenset(mapped_realm_roles),
        client_roles=frozenset(mapped_client_roles),
        tenant_ids=frozenset(tenant_ids),
    )
