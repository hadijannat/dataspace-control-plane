"""Keycloak role name → internal role name mapping.

Keycloak realm roles use kebab-case prefixed names (``dataspace-operator``,
``dataspace-admin``, etc.).  The internal role names are simpler identifiers
used by authorization policies and audit records.

The mapping is explicit and intentional: unknown Keycloak roles are passed
through unchanged (safe default — the authorization engine will not grant
access for unrecognised roles).

Extension
---------
To add new role mappings, extend ``KEYCLOAK_ROLE_MAP`` here and update the
authorization policy in ``ports_impl.py``.  Do not define role semantics
outside ``core/`` — this module only handles name translation.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Role name translation table
# ---------------------------------------------------------------------------

KEYCLOAK_ROLE_MAP: dict[str, str] = {
    "dataspace-operator": "operator",
    "dataspace-admin": "admin",
    "dataspace-viewer": "viewer",
    "dataspace-platform-admin": "platform_admin",
    "dataspace-auditor": "auditor",
    "dataspace-provisioner": "provisioner",
}
"""Maps Keycloak realm role names to internal role identifiers.

Keys: Keycloak realm role name (as returned by ``realm_access.roles`` JWT claim).
Values: Internal role name used by authorization policies and ``OperatorPrincipal``.

Unknown roles are returned unchanged (see ``map_roles``).
"""


# ---------------------------------------------------------------------------
# Mapping functions
# ---------------------------------------------------------------------------


def map_roles(keycloak_roles: list[str]) -> list[str]:
    """Translate a list of Keycloak role names to internal role names.

    Unknown roles are passed through unchanged.  This is intentional: the
    authorization engine will reject unrecognised roles rather than silently
    dropping them, preserving auditability.

    Parameters
    ----------
    keycloak_roles:
        List of role name strings from ``realm_access.roles`` JWT claim.

    Returns
    -------
    list[str]
        Internal role name strings.

    Examples
    --------
    >>> map_roles(["dataspace-operator", "dataspace-admin"])
    ['operator', 'admin']

    >>> map_roles(["some-unknown-role"])
    ['some-unknown-role']
    """
    return [KEYCLOAK_ROLE_MAP.get(r, r) for r in keycloak_roles]


def map_role(keycloak_role: str) -> str:
    """Translate a single Keycloak role name to an internal role name.

    Returns the input unchanged if no mapping is defined.
    """
    return KEYCLOAK_ROLE_MAP.get(keycloak_role, keycloak_role)
