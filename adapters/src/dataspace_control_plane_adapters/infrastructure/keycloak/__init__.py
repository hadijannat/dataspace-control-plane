"""Keycloak human-IAM adapter.

Provides:
- OIDC token verification (JWT, RS256) via python-jose + JWKS cache
- Keycloak Admin REST API client (realm roles, user management)
- Mapping Keycloak identities → core OperatorPrincipal snapshots
- Role-based AuthorizationPort implementation
- Health probe (OIDC discovery endpoint check)

Scope: human operators only.  Machine-to-machine trust (DID, VC, DCP) is
handled by the machine_trust adapter — not here.
"""
