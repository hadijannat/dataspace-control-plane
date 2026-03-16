---
title: "DPP Export Stuck"
summary: "Runbook for diagnosing and recovering from a DPP export workflow stuck in RUNNING state for more than 30 minutes."
owner: infra-lead
last_reviewed: "2026-03-14"
severity: "P2"
affected_services:
  - temporal-workers
  - provisioning-agent
status: approved
---

## Trigger / Alert Source

- **Alert names**: `DPPExportWorkflowStalledAlert`
- **Alert conditions**: `temporal_workflow_running_duration_seconds{workflow_type="DPPExportWorkflow"} > 1800` (30 minutes)
- **Manual trigger**: Operator reports that a passport `status` has been `approved` for over 30 minutes without transitioning to `published`; or `GET /api/v1/passports/{passportId}` returns `lifecycle_state: approved` long after the transition was initiated
- **Typical symptom**: Temporal UI shows `DPPExportWorkflow` in RUNNING state with the last event > 30 minutes ago

## Scope and Blast Radius

**Affected:**

- **The specific passport**: Cannot reach `published` state until the workflow completes or is terminated and resubmitted.
- **EU DPP registry submission**: Delayed — the passport will not appear in the registry until exported.

**NOT affected:**

- **Other passports**: Other DPP export workflows run independently.
- **Catena-X operations**: Contract negotiations and usage metering are independent.
- **Keycloak / Vault / Postgres**: All infrastructure services continue normally.

**Data loss risk**: None — the passport data in Postgres is intact in `approved` state. The export workflow can be retried or resubmitted.

## Pre-Checks

```bash
# Find the stuck workflow ID from the passport ID
kubectl exec -it postgres-0 -n dataspace-infra -- \
  psql -U dataspace -c "SELECT passport_id, lifecycle_state, workflow_id FROM passports WHERE lifecycle_state='approved' AND updated_at < NOW() - INTERVAL '30 minutes';"

# Check temporal-workers health
kubectl get pods -n dataspace-platform | grep temporal-workers
kubectl logs deployment/temporal-workers -n dataspace-platform --tail=50 | grep -E "ERROR|dpp|export"
```

## Triage Checklist

1. [ ] Is the workflow in RUNNING state in Temporal UI? (not FAILED or TIMED_OUT)
2. [ ] What is the last activity in the workflow history? (find where it is stuck)
3. [ ] Is Vault accessible from temporal-workers? (signing activity stall)
4. [ ] Is the EU DPP registry reachable? (registry submission activity stall)
5. [ ] Is BaSyx AAS server reachable? (AAS serialization activity stall)

## Investigation Steps

### Step 1: Locate the workflow in Temporal UI

Navigate to `https://temporal.your-org.internal` → Namespace: `dataspace` → Workflow Type: `DPPExportWorkflow` → Status: `Running`.

Click the stuck workflow and examine the event history:

- **Last event type**: `ActivityTaskScheduled` with the activity type shown
- **Time since last event**: how long the current activity has been running

**Common stuck activities and their causes:**

| Stuck activity | Likely cause | Next step |
|---------------|-------------|-----------|
| `sign_evidence_envelope` | Vault Transit unavailable | See [Vault Transit Failures](../incidents/vault-transit-failures.md) |
| `submit_to_dpp_registry` | EU DPP registry API down or rate-limited | Check Step 3 |
| `serialize_as_aas_shell` | BaSyx AAS server unreachable | Check Step 4 |
| `apply_battery_passport_pack` | Pack validation taking too long (data volume) | Check worker resources |

### Step 2: Check activity retry status

In Temporal UI, if the current activity shows `Attempt: N` (N > 1), it is in retry mode — it has already failed N-1 times. Expand the failed activity events to see the error message.

```bash
# Also check temporal-worker logs for the specific activity error
kubectl logs deployment/temporal-workers -n dataspace-platform --tail=200 | grep -E "dpp_export|submit_to_dpp_registry|serialize_as_aas"
```

### Step 3: Test EU DPP registry connectivity

```bash
kubectl exec -it deployment/temporal-workers -n dataspace-platform -- \
  curl -sk -o /dev/null -w "%{http_code}" \
  https://dpp-registry.ec.europa.eu/api/v1/passports/health
```

Expected: `200`. If timeout or 503: the DPP registry is having an outage. Temporal will retry the activity — this is a transient failure. Wait for the registry to recover (check EU DPP registry status page).

### Step 4: Test BaSyx AAS server connectivity

```bash
kubectl exec -it deployment/temporal-workers -n dataspace-platform -- \
  curl -sk -o /dev/null -w "%{http_code}" \
  http://basyx-aas.dataspace-platform.svc.cluster.local:8080/shells
```

Expected: `200`. If connection refused: BaSyx pod is down.

```bash
kubectl get pods -n dataspace-platform | grep basyx
kubectl rollout restart deployment/basyx-aas -n dataspace-platform
```

## Remediation

### Scenario A: Transient external dependency failure (DPP registry / BaSyx)

If the dependency has recovered, Temporal will automatically retry the activity on the next retry interval. No manual action needed — just wait for the next retry attempt.

Check the retry schedule: in Temporal UI → the activity → "Scheduled time of next attempt" field.

### Scenario B: Activity exceeding maximum retry count (workflow entered FAILED state)

If the workflow has transitioned from RUNNING to FAILED (all retries exhausted):

```bash
# Re-submit the export via the lifecycle transition endpoint with a NEW idempotency key
curl -X POST https://api.your-org.internal/api/v1/passports/<passportId>/lifecycle-transitions \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{"targetState": "published", "reason": "Re-submission after registry outage recovery"}'
```

The workflow re-starts from the beginning. Previously written AAS shells in BaSyx will be overwritten (PUT operation is idempotent).

### Scenario C: Workflow genuinely stuck (no retry attempts for > 30 min)

If the workflow is RUNNING but shows no scheduled retry and no activity completion for > 30 minutes, send a cancellation signal and re-submit:

```bash
# Signal cancellation (workflow will run cleanup activities before ending)
temporal workflow cancel \
  --workflow-id "<workflow-id>" \
  --namespace dataspace

# Wait for workflow to reach CANCELLED state (check Temporal UI)

# Re-submit
curl -X POST https://api.your-org.internal/api/v1/passports/<passportId>/lifecycle-transitions \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{"targetState": "published", "reason": "Re-submission after workflow cancellation"}'
```

## Evidence Capture Requirements

- [ ] Temporal UI screenshot showing the stuck workflow's event history
- [ ] temporal-workers logs from the failure window
- [ ] HTTP response from DPP registry and BaSyx (curl output)
- [ ] Passport ID, workflow ID, and failure timestamp for post-incident tracking

## Related Runbooks

- [Vault Transit Failures](../incidents/vault-transit-failures.md) — if signing activity was the stuck step
- [Temporal Workers Stalled](../incidents/temporal-workers-stalled.md) — if workers are generally not processing
