---
title: "API Reference"
summary: "Overview of the live control-api HTTP surface, stability boundaries, and the split between human guides and machine-derived OpenAPI artifacts."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

The **control-api** is the primary HTTP surface for operator workflows,
automation, workflow status tracking, and management webhooks. It is
implemented with FastAPI and publishes an OpenAPI 3.1 description exported from
the running application contract.

## Stability Model

The current API surface is organized by audience:

| Surface | Prefix | Audience | Stability |
| --- | --- | --- | --- |
| Health probes | `/health/*` | kube probes and operators | stable |
| Operator API | `/api/v1/operator/*` | browser and operator tooling | stable |
| Public automation API | `/api/v1/public/*` | machine clients | stable |
| Workflow streams | `/api/v1/streams/*` | real-time clients | stable |
| Management webhooks | `/api/v1/webhooks/*` | upstream integrations | stable |
| UI runtime config | `/ui/runtime-config.json` | web-console bootstrap | implementation detail |

## Current Endpoint Groups

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health/live` | liveness probe |
| `GET` | `/health/ready` | readiness probe with dependency snapshot |
| `GET` | `/api/v1/operator/tenants/` | paginated tenant listing |
| `GET` | `/api/v1/operator/tenants/{tenant_id}` | tenant details for an authorized tenant |
| `POST` | `/api/v1/operator/procedures/start` | operator-scoped workflow start |
| `GET` | `/api/v1/operator/procedures/` | paginated procedure listing by tenant |
| `GET` | `/api/v1/operator/procedures/{workflow_id}` | workflow status lookup |
| `POST` | `/api/v1/public/procedures/start` | automation-facing workflow start |
| `GET` | `/api/v1/public/procedures/{workflow_id}` | public workflow status lookup |
| `POST` | `/api/v1/streams/tickets` | mint an SSE stream ticket |
| `GET` | `/api/v1/streams/workflows/{workflow_id}` | SSE workflow status stream |
| `POST` | `/api/v1/webhooks/management` | signed inbound management webhook |

## Guides

- [Authentication](guides/auth.md)
- [Idempotency](guides/idempotency.md)
- [Pagination and Filtering](guides/pagination-filtering.md)
- [Workflow Handles](guides/workflows.md)
- [Server-Sent Events](guides/sse.md)
- [Error Model](guides/error-model.md)

## Machine-Derived Reference

The committed API artifacts live under [`api/openapi/`](openapi/index.md):

- `source/` is the canonical exported OpenAPI 3.1 spec from the FastAPI app
- `bundled/` is the Redocly-bundled single-file artifact committed for review
- `generated/` is reserved for CI-only rendered outputs and is not versioned

Use the human guides for behavior, expectations, and client patterns. Use the
OpenAPI files for exact wire shapes and generated client workflows.
