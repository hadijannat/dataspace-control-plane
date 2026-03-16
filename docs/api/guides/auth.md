---
title: "Authentication Guide"
summary: "Bearer-token and stream-ticket authentication for operator, public, and streaming control-api endpoints."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

The control-api authenticates most requests with Keycloak-issued Bearer JWTs.
The workflow stream endpoint also supports short-lived stream tickets so browser
clients can subscribe without custom headers.

## Bearer JWT Validation

Bearer authentication is enforced by `get_current_principal()` and
`validate_token()` in the control-api auth layer.

The API validates:

- signature against the issuer JWKS
- `aud` against `CONTROL_API_OIDC_AUDIENCE`
- `iss` against `CONTROL_API_OIDC_ISSUER`

On success, the token becomes a `Principal` with:

| Claim source | Principal field | Notes |
| --- | --- | --- |
| `sub` | `subject` | stable caller identity |
| `email` | `email` | optional |
| `realm_access.roles` | `realm_roles` | includes `dataspace-admin` when present |
| `resource_access[control-api].roles` | `client_roles` | client-scoped roles |
| `tenant_ids` | `tenant_ids` | tenant access set enforced by API logic |

## Operator and Public Endpoints

Both `/api/v1/operator/*` and `/api/v1/public/*` require `Authorization:
Bearer ...`.

Authorization is tenant-aware:

- callers may only act on tenants included in `tenant_ids`
- realm role `dataspace-admin` bypasses tenant-specific filtering
- workflow lookups and stream subscriptions are denied if the resolved workflow
  tenant is outside the principal scope

## Workflow Stream Authentication

`GET /api/v1/streams/workflows/{workflow_id}` supports two modes:

1. standard Bearer auth
2. query-string `ticket` auth minted by `POST /api/v1/streams/tickets`

Stream tickets are HMAC-signed, short-lived envelopes containing:

- caller subject
- caller email
- realm roles
- client roles
- tenant IDs
- expiration timestamp

Use tickets for browser flows that cannot easily attach custom headers to SSE
requests.

## Human vs Machine Flows

The repo assumes two common patterns:

- human operator flow: web-console obtains a Keycloak access token and calls the
  operator endpoints
- machine flow: automation obtains a service-account token and calls the public
  API or webhook-related endpoints

The docs layer does not currently define additional per-role policy beyond what
the application enforces in `Principal.can_access_tenant()` and the
`dataspace-admin` override.
