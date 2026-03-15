"""Keycloak implementation of core/domains/operator_access/ports.py :: AuthorizationPort.

Satisfies
---------
- ``core/domains/operator_access/ports.py :: AuthorizationPort``  — via ``KeycloakAuthorizationPort``

Design
------
The authorization decision is **local** (no Keycloak API call at decision time):
1. The caller presents an ``OperatorPrincipal`` (already verified by OidcVerifier).
2. We evaluate the principal's ``realm_roles`` against a role-action-scope matrix.
3. A positive decision is returned if any role grants the requested action on the
   requested scope.

This keeps the hot path (every API request) free of remote I/O.  Roles are
loaded once at token verification time and embedded in the principal snapshot.

Role-action-scope matrix
------------------------
The matrix below is the default policy.  Extend ``ROLE_ACTION_MATRIX`` for
additional roles or actions.  Do not change semantics here — core policy lives
in ``core/``.

    platform_admin  → all actions on all scopes
    admin           → read, write, approve on tenant scope
    operator        → read, write, execute on tenant scope
    provisioner     → execute on site + environment scopes
    auditor         → read on all scopes
    viewer          → read on all scopes
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Role-action-scope matrix
# ---------------------------------------------------------------------------

# Structure: role_name → set of (action, resource_type) tuples
# resource_type "*" means any resource type is permitted.
_ACTION_WILDCARD = "*"
_SCOPE_WILDCARD = "*"

ROLE_ACTION_MATRIX: dict[str, list[tuple[str, str]]] = {
    "platform_admin": [(_ACTION_WILDCARD, _SCOPE_WILDCARD)],
    "admin": [
        ("read", _SCOPE_WILDCARD),
        ("write", "tenant"),
        ("approve", "tenant"),
        ("admin", "tenant"),
    ],
    "operator": [
        ("read", _SCOPE_WILDCARD),
        ("write", "tenant"),
        ("write", "legal_entity"),
        ("execute", "tenant"),
        ("execute", "legal_entity"),
    ],
    "provisioner": [
        ("read", _SCOPE_WILDCARD),
        ("execute", "site"),
        ("execute", "environment"),
        ("write", "site"),
        ("write", "environment"),
    ],
    "auditor": [("read", _SCOPE_WILDCARD)],
    "viewer": [("read", _SCOPE_WILDCARD)],
}
"""Default role-action-scope authorization matrix.

Modify this mapping to tune authorization policy.  Each entry is a list of
``(action, resource_type)`` tuples; ``"*"`` in either position acts as a
wildcard.
"""


class KeycloakAuthorizationPort:
    """Role-based authorization evaluator backed by Keycloak realm roles.

    Implements ``core/domains/operator_access/ports.py :: AuthorizationPort``.

    Decision is **synchronous** — no I/O, no external calls.  The principal's
    roles are embedded in the ``OperatorPrincipal`` snapshot, which was built
    from a pre-verified JWT by ``OidcVerifier`` + ``claims_to_principal``.

    Parameters
    ----------
    role_action_matrix:
        Override the default ``ROLE_ACTION_MATRIX`` for custom policy rules.
        Pass ``None`` to use the built-in defaults.
    """

    def __init__(
        self, role_action_matrix: dict[str, list[tuple[str, str]]] | None = None
    ) -> None:
        self._matrix = role_action_matrix or ROLE_ACTION_MATRIX

    def decide(
        self, principal: Any, action: str, scope: Any
    ) -> Any:  # AuthorizationDecision
        """Evaluate whether the principal is allowed to perform action on scope.

        Parameters
        ----------
        principal:
            ``OperatorPrincipal`` from ``claims_to_principal``.
        action:
            Action string, e.g. ``"read"``, ``"write"``, ``"execute"``,
            ``"approve"``, ``"admin"``.
        scope:
            ``Scope`` value object with ``resource_type`` and optional ``resource_id``.

        Returns
        -------
        AuthorizationDecision
            ``allowed=True`` with the matching role name as ``grant_id``, or
            ``allowed=False`` with a denial reason.
        """
        from dataspace_control_plane_core.domains.operator_access.model.aggregates import (  # noqa: PLC0415
            AuthorizationDecision,
        )

        # Combine realm_roles and client_roles for evaluation.
        principal_roles: frozenset[str] = principal.realm_roles | principal.client_roles
        resource_type: str = scope.resource_type

        for role_name in principal_roles:
            permitted_actions = self._matrix.get(role_name, [])
            for allowed_action, allowed_resource_type in permitted_actions:
                action_match = (allowed_action == _ACTION_WILDCARD) or (allowed_action == action)
                scope_match = (
                    allowed_resource_type == _SCOPE_WILDCARD
                    or allowed_resource_type == resource_type
                )
                if action_match and scope_match:
                    logger.debug(
                        "AuthorizationDecision ALLOW: subject=%s role=%s action=%s scope=%s",
                        principal.subject,
                        role_name,
                        action,
                        resource_type,
                    )
                    return AuthorizationDecision(
                        allowed=True,
                        reason=f"Role '{role_name}' permits '{action}' on '{resource_type}'",
                        grant_id=role_name,  # role name used as synthetic grant reference
                    )

        logger.debug(
            "AuthorizationDecision DENY: subject=%s roles=%s action=%s scope=%s",
            principal.subject,
            principal_roles,
            action,
            resource_type,
        )
        return AuthorizationDecision(
            allowed=False,
            reason=(
                f"No role in {set(principal_roles)!r} grants '{action}' "
                f"on resource_type='{resource_type}'"
            ),
            grant_id=None,
        )
