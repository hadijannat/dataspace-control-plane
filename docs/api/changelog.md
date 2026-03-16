---
title: "API Changelog"
summary: "Change history for the current control-api HTTP surface and its exported OpenAPI contract."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

## v0.2.0 (2026-03-16)

This hardening pass aligned the published contract with the explicit procedure
registry, durable idempotency store, canonical runtime status model, and
workflow-scoped stream ticket behavior.

### Behavior Changes

- start endpoints now reject unknown payload fields with `422`
- accepted workflow handles now use lowercase canonical status values such as
  `running`
- idempotency is now durable and scoped by tenant, procedure type, and
  idempotency key, with `409` on same-key/different-payload reuse
- business-key workflow IDs are generated from the procedure manifest rather
  than the raw HTTP idempotency key
- stream tickets are issued for one workflow only and require `workflow_id` in
  the ticket mint request body
- management webhooks are mounted only when
  `CONTROL_API_WEBHOOK_SHARED_SECRET` is configured

## v0.1.0 (2026-03-16)

This docs-as-code baseline aligns the published API docs with the live FastAPI
surface.

### Documented Endpoints

| Method | Path |
| --- | --- |
| `GET` | `/health/live` |
| `GET` | `/health/ready` |
| `GET` | `/api/v1/operator/tenants/` |
| `GET` | `/api/v1/operator/tenants/{tenant_id}` |
| `POST` | `/api/v1/operator/procedures/start` |
| `GET` | `/api/v1/operator/procedures/` |
| `GET` | `/api/v1/operator/procedures/{workflow_id}` |
| `POST` | `/api/v1/public/procedures/start` |
| `GET` | `/api/v1/public/procedures/{workflow_id}` |
| `POST` | `/api/v1/streams/tickets` |
| `GET` | `/api/v1/streams/workflows/{workflow_id}` |

### Notable Corrections

- replaced the previous speculative company/contract/passport API narrative with
  the current procedure- and tenant-oriented surface
- documented stream-ticket authentication for SSE
- documented the current scaffold error behavior instead of an unimplemented
  RFC 7807 contract
- switched the committed OpenAPI source to the exported FastAPI contract
