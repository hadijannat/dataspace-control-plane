---
title: "Workflow Handles Guide"
summary: "How to work with long-running Temporal workflow handles returned by 202 Accepted responses: polling, cancellation, and webhook callbacks."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Workflow Handles Guide

Operations that start Temporal workflows return `202 Accepted` immediately with a **workflow handle** — a lightweight reference that clients use to track and manage the long-running operation.

## Workflow Handle Structure

```json
{
  "workflowId": "tenant-acme-001:onboarding:BPNL000000000001",
  "runId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "statusUrl": "/api/v1/companies/BPNL000000000001"
}
```

| Field | Description |
|-------|-------------|
| `workflowId` | Temporal workflow ID. Format: `{tenant_id}:{workflow_type}:{entity_id}`. Stable across retries — the same logical operation always uses the same workflow ID. |
| `runId` | Temporal run ID for this specific execution. Changes on each restart. Use for Temporal UI lookup. |
| `statusUrl` | The resource URL to poll for completion status. This is the canonical resource URL (e.g., `/api/v1/companies/{companyId}`), not a separate workflow status endpoint. |

## Polling for Completion

Poll the `statusUrl` until the resource reaches a terminal state:

```python
import asyncio
import httpx

async def wait_for_company_onboarding(
    client: httpx.AsyncClient,
    status_url: str,
    timeout_seconds: float = 120.0,
) -> dict:
    """Poll statusUrl until company status is provisioned or failed."""
    deadline = asyncio.get_event_loop().time() + timeout_seconds
    poll_interval = 2.0  # seconds

    while asyncio.get_event_loop().time() < deadline:
        response = await client.get(
            status_url,
            headers={"Authorization": f"Bearer {await get_token()}"},
        )
        response.raise_for_status()
        company = response.json()

        match company["status"]:
            case "provisioned":
                return company
            case "failed":
                raise RuntimeError(f"Onboarding failed: {company}")
            case "provisioning":
                await asyncio.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, 10.0)  # back off gradually
            case _:
                raise RuntimeError(f"Unexpected status: {company['status']}")

    raise TimeoutError(f"Onboarding did not complete within {timeout_seconds}s")
```

## Workflow Statuses

Temporal workflow terminal states as mapped to resource statuses:

| Temporal state | Resource status | Meaning |
|---------------|-----------------|---------|
| `RUNNING` | `provisioning` / `under_review` / etc. | Workflow is executing |
| `COMPLETED` | `provisioned` / `published` / `finalized` | Workflow completed successfully |
| `FAILED` | `failed` | Workflow failed — check workflow history |
| `TIMED_OUT` | `failed` | Workflow exceeded its timeout |
| `TERMINATED` | `failed` | Workflow was manually terminated |
| `CANCELLED` | `failed` | Workflow was cancelled |
| `CONTINUED_AS_NEW` | (previous state) | Workflow continued — polling continues |

## Workflow ID Format

Workflow IDs follow the format: `{tenant_id}:{workflow_type}:{entity_id}`

| Workflow type | Example workflow ID |
|--------------|-------------------|
| `onboarding` | `tenant-acme-001:onboarding:BPNL000000000001` |
| `negotiation` | `tenant-acme-001:negotiation:a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `dpp-export` | `tenant-acme-001:dpp-export:passport-uuid` |
| `dpp-recall` | `tenant-acme-001:dpp-recall:passport-uuid` |

The workflow ID is deterministic given the tenant and entity — submitting the same onboarding request twice with different `runId`s will return the same `workflowId`. Combined with idempotency keys, this prevents duplicate workflows for the same entity.

## Workflow Cancellation

To cancel a running workflow (e.g., to abort a stuck DPP export), send a `DELETE` to the resource URL with a `reason` query parameter:

```http
DELETE /api/v1/passports/{passportId}/lifecycle-transitions?reason=operator-abort
Authorization: Bearer {token}
```

This sends a Temporal `CancelWorkflow` signal. The workflow's cleanup activities run before the workflow enters `CANCELLED` state. The resource status transitions to `failed` once cancellation is complete.

!!! warning "Cancellation is not immediate"
    Temporal workflows handle cancellation gracefully — they run cleanup activities before terminating. For immediate termination (no cleanup), use the Temporal UI or `temporal workflow terminate`. Termination should be used only in emergency situations.

## Webhook Callback (Optional)

If a `callbackUrl` is provided in the request body, the control-api sends a `POST` to that URL when the workflow completes:

```json
{
  "event": "workflow_completed",
  "workflowId": "tenant-acme-001:onboarding:BPNL000000000001",
  "runId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "provisioned",
  "resourceUrl": "/api/v1/companies/BPNL000000000001",
  "timestamp": "2026-03-14T12:34:56Z"
}
```

The callback payload is signed with the tenant's Vault Transit key. Verify the `X-Signature` header before processing the callback.

Callback URLs must be HTTPS and reachable from within the platform network. Callbacks are retried up to 3 times with exponential backoff on failure.

## Temporal UI Access

For debugging, the Temporal UI is available at `https://temporal.your-org.internal` (internal network only). Look up a workflow by its `workflowId` or `runId` to inspect the full event history, activity results, and failure details.

Access to the Temporal UI requires the `operator` role in Keycloak (enforced by Nginx ingress authentication).
