---
title: "Server-Sent Events Guide"
summary: "Real-time workflow progress streaming via Server-Sent Events — event format, types, browser usage, and reconnection behavior."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Server-Sent Events Guide

The control-api provides Server-Sent Events (SSE) for real-time workflow progress streaming. Instead of polling the `statusUrl`, clients can subscribe to a live event stream for any active workflow.

## SSE Endpoint

```http
GET /api/v1/workflows/{workflowId}/events
Authorization: Bearer {token}
Accept: text/event-stream
```

The `workflowId` is the value returned in the `202 Accepted` workflow handle (e.g., `tenant-acme-001:onboarding:BPNL000000000001`).

**Response headers:**

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

The connection remains open until the workflow reaches a terminal state (`COMPLETED`, `FAILED`, `CANCELLED`, `TERMINATED`), at which point the server closes the stream.

## Event Format

Each event follows the SSE specification (`data:` line, optional `event:` line, optional `id:` line):

```
id: 1710000001234
event: ACTIVITY_COMPLETED
data: {"type":"ACTIVITY_COMPLETED","activityType":"create_keycloak_realm","tenantId":"tenant-acme-001","timestamp":"2026-03-14T12:34:01Z","durationMs":342}

id: 1710000002567
event: ACTIVITY_COMPLETED
data: {"type":"ACTIVITY_COMPLETED","activityType":"sign_did_document","tenantId":"tenant-acme-001","timestamp":"2026-03-14T12:34:02Z","durationMs":18}

id: 1710000003891
event: WORKFLOW_COMPLETED
data: {"type":"WORKFLOW_COMPLETED","workflowId":"tenant-acme-001:onboarding:BPNL000000000001","status":"provisioned","timestamp":"2026-03-14T12:34:03Z","resourceUrl":"/api/v1/companies/BPNL000000000001"}

```

## Event Types

| Event type | Trigger | Key payload fields |
|-----------|---------|-------------------|
| `WORKFLOW_STARTED` | Workflow execution begins | `workflowId`, `workflowType`, `tenantId`, `timestamp` |
| `ACTIVITY_STARTED` | An activity begins executing | `workflowId`, `activityType`, `attempt`, `timestamp` |
| `ACTIVITY_COMPLETED` | An activity completes successfully | `workflowId`, `activityType`, `durationMs`, `timestamp` |
| `ACTIVITY_FAILED` | An activity fails (may be retried) | `workflowId`, `activityType`, `error`, `attempt`, `nextRetryAt`, `timestamp` |
| `WORKFLOW_COMPLETED` | Workflow reaches COMPLETED terminal state | `workflowId`, `status`, `resourceUrl`, `timestamp` |
| `WORKFLOW_FAILED` | Workflow reaches FAILED terminal state | `workflowId`, `error`, `failedActivity`, `timestamp` |
| `WORKFLOW_CANCELLED` | Workflow was cancelled | `workflowId`, `reason`, `timestamp` |

!!! note "Security note"
    Activity payload details (e.g., intermediate Keycloak responses) are **not** included in SSE events. Events include only the activity type name, timing, and success/failure status. This prevents sensitive intermediate data from being exposed via the event stream.

## Browser Usage (EventSource API)

```javascript
const workflowId = "tenant-acme-001:onboarding:BPNL000000000001";
const token = await getAccessToken(); // from Keycloak JS adapter

// EventSource does not support custom headers natively —
// pass the token as a query parameter (the server verifies it the same way)
const eventSource = new EventSource(
  `/api/v1/workflows/${encodeURIComponent(workflowId)}/events?access_token=${token}`
);

eventSource.addEventListener("WORKFLOW_COMPLETED", (event) => {
  const data = JSON.parse(event.data);
  console.log("Onboarding complete:", data.resourceUrl);
  eventSource.close();
  // Fetch the final resource
  fetchCompany(data.resourceUrl);
});

eventSource.addEventListener("ACTIVITY_COMPLETED", (event) => {
  const data = JSON.parse(event.data);
  updateProgressBar(data.activityType);
});

eventSource.addEventListener("WORKFLOW_FAILED", (event) => {
  const data = JSON.parse(event.data);
  console.error("Onboarding failed:", data.error);
  eventSource.close();
  showErrorDialog(data.error);
});

eventSource.onerror = (error) => {
  console.warn("SSE connection error — browser will reconnect automatically");
};
```

## Reconnection

The browser's `EventSource` automatically reconnects after a connection drop. On reconnection, the browser sends the `Last-Event-ID` header with the last received event ID. The control-api resumes the stream from that event ID, ensuring no events are missed.

```http
GET /api/v1/workflows/{workflowId}/events
Authorization: Bearer {token}
Last-Event-ID: 1710000001234
```

Events are buffered in memory for up to 5 minutes after emission to support reconnection. If the reconnection occurs more than 5 minutes after the last event, the stream restarts from the current state (a synthetic `WORKFLOW_STARTED` or current activity event is sent first).

## Python Client Usage

```python
import httpx
import json

async def stream_workflow_events(workflow_id: str, token: str):
    """Stream workflow events using httpx async streaming."""
    url = f"/api/v1/workflows/{workflow_id}/events"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(base_url="https://api.your-org.internal") as client:
        async with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    yield event_data
                    if event_data["type"] in ("WORKFLOW_COMPLETED", "WORKFLOW_FAILED"):
                        return  # Stream will close after terminal event
```

## Limitations

- SSE connections count against the control-api's connection limit. Do not hold open SSE connections for workflows that have already reached a terminal state.
- The SSE endpoint does not support `POST` — it is read-only. To send signals to a workflow (e.g., cancellation), use the REST endpoint.
- SSE authentication via `access_token` query parameter is an exception to the header-based auth rule — necessary because `EventSource` does not support custom headers. The token is validated identically to Bearer header auth. Short-lived tokens (5-minute TTL) will expire during long-running workflows — the client should close and re-open the SSE connection with a fresh token before expiry.
