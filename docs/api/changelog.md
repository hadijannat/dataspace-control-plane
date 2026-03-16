---
title: "API Changelog"
summary: "Change history for the current control-api HTTP surface and its exported OpenAPI contract."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

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
| `POST` | `/api/v1/webhooks/management` |

### Notable Corrections

- replaced the previous speculative company/contract/passport API narrative with
  the current procedure- and tenant-oriented surface
- documented stream-ticket authentication for SSE
- documented the current scaffold error behavior instead of an unimplemented
  RFC 7807 contract
- switched the committed OpenAPI source to the exported FastAPI contract
