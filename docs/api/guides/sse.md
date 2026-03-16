---
title: "Server-Sent Events Guide"
summary: "Real-time workflow status streaming over `/api/v1/streams/workflows/{workflow_id}`, including Bearer and ticket-based auth."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

The control-api exposes workflow progress over Server-Sent Events at:

```http
GET /api/v1/streams/workflows/{workflow_id}
```

## Authentication Options

The stream endpoint accepts either:

- `Authorization: Bearer {token}`
- `?ticket={stream_ticket}` where the ticket comes from
  `POST /api/v1/streams/tickets`

Ticket authentication exists specifically for clients that prefer not to manage
custom headers for SSE connections.

## Event Shape

The stream emits `status` events whose payload is a serialized workflow status
snapshot derived from shared workflow state.

Example stream:

```text
event: status
data: {"workflow_id":"tenant-a:company-onboarding:123","status":"RUNNING","tenant_id":"tenant-a"}

event: status
data: {"workflow_id":"tenant-a:company-onboarding:123","status":"COMPLETED","tenant_id":"tenant-a","result":{"outcome":"ok"}}
```

## Browser Pattern

1. call `POST /api/v1/streams/tickets`
2. open `EventSource("/api/v1/streams/workflows/{workflow_id}?ticket=...")`
3. close the stream once a terminal status arrives

## Authorization Rules

Before the stream opens, the API loads the referenced workflow snapshot and
verifies that the authenticated principal can access the workflow tenant. The
endpoint returns:

- `401` when no valid Bearer token or stream ticket is present
- `403` when the workflow exists but belongs to an inaccessible tenant
- `404` when the workflow is unknown
- `503` when neither workflow runtime nor read-model state is available

## When to Use SSE

Prefer SSE over repeated polling when:

- the UI needs live progress updates
- a workflow is long-running
- you want a single server-side subscription rather than short GET bursts

Prefer the poll endpoint when the caller only needs a final completion check.
