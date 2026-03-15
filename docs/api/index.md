---
title: "API Reference"
summary: "Overview of the control-api HTTP REST surface, versioning policy, authentication, idempotency, and links to the OpenAPI spec and guides."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# API Reference

The **control-api** is the primary HTTP interface for the Dataspace Control Plane. It is implemented with FastAPI (Python 3.12) and served via Uvicorn. The API follows REST conventions with JSON request and response bodies, URL-based versioning, RFC 7807 Problem Details error responses, and idempotency key support on all mutation endpoints.

## Versioning

All stable endpoints are served under `/api/v1/`. Backward-compatible additions (new optional fields, new response properties, new query parameters) are made within the same version without a version bump. Breaking changes (removed fields, changed semantics, changed error responses) require a new version prefix (`/api/v2/`).

| Prefix | Stability | Purpose |
|--------|-----------|---------|
| `/api/v1/` | Stable | Production-grade endpoints. Changes follow backward-compatibility rules. |
| `/api/v1/internal/` | Unstable | Internal platform endpoints used by temporal-workers and provisioning-agent. May change without notice. |
| `/api/health` | Stable | Liveness and readiness probes (no version prefix — required by Kubernetes) |

## Authentication

All requests to `/api/v1/` require a valid Bearer JWT issued by Keycloak. Unauthenticated requests receive `401 Unauthorized` with a Problem Details body (`/errors/authentication-required`).

See the [Authentication Guide](guides/auth.md) for:
- Human operator flow (Authorization Code + PKCE)
- Service-to-service flow (client_credentials)
- Required Keycloak roles per endpoint
- Token structure and claims

## Idempotency

All `POST`, `PATCH`, and `DELETE` endpoints accept an `Idempotency-Key: <uuid-v4>` header. Requests with the same key from the same tenant within a 24-hour TTL window receive the cached response. This enables safe retry without duplicating side effects.

See the [Idempotency Guide](guides/idempotency.md) for the full contract.

## Long-Running Operations

Operations that start a Temporal workflow return `202 Accepted` immediately with a workflow handle: `{"workflowId": "...", "runId": "...", "statusUrl": "..."}`. Poll the `statusUrl` for completion.

See the [Workflow Handles Guide](guides/workflows.md) and [Server-Sent Events Guide](guides/sse.md) for alternatives to polling.

## Error Model

All error responses use [RFC 7807 Problem Details](https://datatracker.ietf.org/doc/html/rfc7807) format:

```json
{
  "type": "/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "Field 'legalEntityId' is required.",
  "instance": "/api/v1/companies",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "validationErrors": [
    {"field": "legalEntityId", "message": "Field is required"}
  ]
}
```

See the [Error Model Guide](guides/error-model.md) for the full type URI table.

## OpenAPI Specification

The OpenAPI 3.1 specification is the authoritative machine-readable contract for all control-api endpoints. FastAPI generates the spec from the route definitions; the committed source spec in `docs/api/openapi/source/control-api.yaml` is the design-time reference.

See [OpenAPI Reference](openapi/index.md) for the spec location, bundling workflow, and Redocly linting commands.

## Quick Endpoint Index

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/health/ready` | Readiness probe |
| `POST` | `/api/v1/companies` | Register a new company (starts OnboardingWorkflow) |
| `GET` | `/api/v1/companies/{companyId}` | Get company details |
| `POST` | `/api/v1/usage-events` | Record a usage event |
| `GET` | `/api/v1/usage-events` | List usage events (paginated) |
| `POST` | `/api/v1/contracts/negotiations` | Start a contract negotiation |
| `GET` | `/api/v1/contracts/negotiations/{negotiationId}` | Get negotiation status |
| `POST` | `/api/v1/passports` | Create a new DPP passport |
| `GET` | `/api/v1/passports/{passportId}` | Get passport details |
| `POST` | `/api/v1/passports/{passportId}/lifecycle-transitions` | Transition passport lifecycle state |
