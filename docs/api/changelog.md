---
title: "API Changelog"
summary: "Version history for the control-api, including new endpoints, breaking changes, and deprecations."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# API Changelog

This changelog documents all API version increments, new endpoints, breaking changes, and deprecations for the control-api. Changes within a stable version (`/api/v1/`) are backward-compatible additions. Breaking changes introduce a new version prefix.

## v0.1.0 (2026-03-14)

**Initial API surface.** This is the first committed version of the control-api specification. All endpoints listed here are new.

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness probe — returns `{"status": "ok"}` if the process is running |
| `GET` | `/api/health/ready` | Readiness probe — checks Postgres, Temporal, and Vault connectivity |
| `POST` | `/api/v1/companies` | Register a new company (starts OnboardingWorkflow) |
| `GET` | `/api/v1/companies/{companyId}` | Get company details by legal entity ID |
| `POST` | `/api/v1/usage-events` | Record a usage event for an active contract agreement |
| `GET` | `/api/v1/usage-events` | List usage events for the authenticated tenant (paginated) |
| `POST` | `/api/v1/contracts/negotiations` | Start a contract negotiation workflow |
| `GET` | `/api/v1/contracts/negotiations/{negotiationId}` | Get negotiation status |
| `POST` | `/api/v1/passports` | Create a new Digital Product Passport in draft state |
| `GET` | `/api/v1/passports/{passportId}` | Get passport details and lifecycle state |
| `POST` | `/api/v1/passports/{passportId}/lifecycle-transitions` | Transition passport lifecycle state |

### Error Model

RFC 7807 Problem Details format adopted for all error responses. See [Error Model Guide](guides/error-model.md).

### Authentication

Keycloak Bearer JWT authentication required on all `/api/v1/` endpoints. See [Authentication Guide](guides/auth.md).

### Idempotency

`Idempotency-Key` header supported on all `POST` endpoints. Per-tenant, 24-hour TTL. See [Idempotency Guide](guides/idempotency.md).

### Workflow Handles

Long-running operations return `202 Accepted` with `{workflowId, runId, statusUrl}`. SSE streaming available at `/api/v1/workflows/{workflowId}/events`. See [Workflow Handles Guide](guides/workflows.md).

---

## Upcoming (planned for v0.2.0)

The following additions are planned for the next release. They are documented here for early visibility — do not implement against these specs until they are in an official release.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/contracts/agreements` | List all finalized contract agreements |
| `GET` | `/api/v1/contracts/agreements/{agreementId}` | Get agreement details |
| `GET` | `/api/v1/passports` | List passports (paginated, with lifecycle state filter) |
| `GET` | `/api/v1/workflows/{workflowId}/events` | SSE stream for workflow progress |
| `DELETE` | `/api/v1/passports/{passportId}/lifecycle-transitions` | Cancel an in-progress lifecycle transition |
| `POST` | `/api/v1/credentials` | Issue a Verifiable Credential |
| `GET` | `/api/v1/credentials/{credentialId}` | Get credential details |
