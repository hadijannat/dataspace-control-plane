---
title: "Workflow Handles Guide"
summary: "How the control-api returns accepted workflow handles and how callers should poll or stream procedure status."
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
  "workflow_id": "tenant-a:company-onboarding:123",
  "procedure_type": "company-onboarding",
  "tenant_id": "tenant-a",
  "status": "STARTED",
  "poll_url": "/api/v1/operator/procedures/tenant-a:company-onboarding:123",
  "stream_url": "/api/v1/streams/workflows/tenant-a:company-onboarding:123",
  "correlation_id": "2c8f..."
}
```

Public start:

```json
{
  "workflow_id": "tenant-a:company-onboarding:123",
  "status": "STARTED",
  "poll_url": "/api/v1/public/procedures/tenant-a:company-onboarding:123",
  "stream_url": "/api/v1/streams/workflows/tenant-a:company-onboarding:123",
  "correlation_id": "2c8f..."
}
```

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
- `result`
- `failure_message`
- `search_attributes`
- `started_at`
- `updated_at`

## Listing Procedures

Operators can also browse workflow history with:

```http
GET /api/v1/operator/procedures/?tenant_id=tenant-a&status=RUNNING&limit=20&offset=0
Authorization: Bearer {token}
```

This list is backed by the read-model projection and is suitable for operator
UI tables, not for low-latency workflow progress.

## Recommended Client Pattern

- use the accepted response `poll_url` for deterministic workflow tracking
- switch to the `stream_url` when you need live status updates
- use the list endpoint for dashboards and operator browsing, not as the
  primary completion detector for a single workflow

## Current Non-Features

The current scaffold does **not** document a public workflow cancellation API or
callback delivery contract. If those surfaces are added later, they should be
documented here and exported into the OpenAPI contract at the same time.
