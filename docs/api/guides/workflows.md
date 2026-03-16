---
title: "Workflow Handles Guide"
summary: "How the control-api returns accepted workflow handles, assigns business-key workflow IDs, and exposes canonical procedure runtime state."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

Procedure-start endpoints return immediately and hand the caller a workflow
handle instead of blocking on completion.

## Accepted Response Shapes

Operator start:

```json
{
  "workflow_id": "company-onboarding:tenant-a:LE-123",
  "procedure_type": "company-onboarding",
  "tenant_id": "tenant-a",
  "status": "running",
  "poll_url": "/api/v1/operator/procedures/company-onboarding:tenant-a:LE-123",
  "stream_url": "/api/v1/streams/workflows/company-onboarding:tenant-a:LE-123",
  "correlation_id": "2c8f..."
}
```

Public start:

```json
{
  "workflow_id": "company-onboarding:tenant-a:LE-123",
  "status": "running",
  "poll_url": "/api/v1/public/procedures/company-onboarding:tenant-a:LE-123",
  "stream_url": "/api/v1/streams/workflows/company-onboarding:tenant-a:LE-123",
  "correlation_id": "2c8f..."
}
```

Workflow IDs come from the procedure manifest, not from the HTTP idempotency
key. For entity-lifecycle procedures such as `company-onboarding`, that means
the workflow ID is the business key:

```text
company-onboarding:{tenant_id}:{legal_entity_id}
```

If a start request reuses an active business key, the API returns `409` rather
than launching a second copy of the same entity workflow.

## Polling Endpoints

| Audience | Poll path | Response shape |
| --- | --- | --- |
| operator | `/api/v1/operator/procedures/{workflow_id}` | `ProcedureStatusDTO` |
| automation | `/api/v1/public/procedures/{workflow_id}` | `ProcedureStatusDTO` |

The status DTO carries:

- `workflow_id`
- `procedure_type`
- `tenant_id`
- `status`
- `phase`
- `progress_percent`
- `result`
- `failure_message`
- `search_attributes`
- `links`
- `started_at`
- `updated_at`

Status values are lowercase canonical values such as `running`, `completed`,
`failed`, `cancelled`, and `timed_out`.

For running workflows, the API prefers the workflow query result so phase and
progress changes are visible before the projection catches up. The Postgres
projection remains the fallback path for coarse status lookup and list pages.

## Listing Procedures

Operators can also browse workflow history with:

```http
GET /api/v1/operator/procedures/?tenant_id=tenant-a&status=running&limit=20&offset=0
Authorization: Bearer {token}
```

This list is backed by the read-model projection and is suitable for operator
UI tables, not for low-latency workflow progress.

## Recommended Client Pattern

- use the accepted response `poll_url` for deterministic workflow tracking
- switch to the `stream_url` when you need live status updates
- use the list endpoint for dashboards and operator browsing, not as the
  primary completion detector for a single workflow
- expect `422` if the submitted payload contains fields the procedure
  definition does not declare

## Current Non-Features

The current scaffold does **not** document a public workflow cancellation API or
callback delivery contract. If those surfaces are added later, they should be
documented here and exported into the OpenAPI contract at the same time.
