---
title: "Temporal Workers Stalled"
summary: "Runbook for diagnosing and recovering from Temporal worker stalls — task queue backlog, worker crash loops, Temporal Server connectivity issues, or Vault dependencies blocking activities."
owner: infra-lead
last_reviewed: "2026-03-14"
severity: "P1"
affected_services:
  - temporal-workers
  - control-api
  - provisioning-agent
status: approved
---

# Temporal Workers Stalled

## Trigger / Alert Source

- **Alert names**: `TemporalTaskQueueBacklogHigh`, `TemporalWorkflowCompletionRateZero`, `TemporalWorkerPodCrashLoopBackOff`
- **Alert conditions**: `temporal_task_queue_backlog{namespace="dataspace"} > 50` for > 5 minutes OR no `workflow_completed` metric in 5 minutes during business hours
- **Manual trigger**: Operators report that company onboarding or DPP export workflows have been in RUNNING state for > 30 minutes without activity
- **Typical symptom**: Temporal UI shows multiple workflows in RUNNING state with no recent workflow completions; task queue backlog counter rising

## Scope and Blast Radius

**Affected when workers are stalled:**

- **temporal-workers**: All Temporal workflow activities queue but do not execute. Workflows accumulate in RUNNING state.
- **control-api**: `202 Accepted` responses are returned for new workflow starts, but no progress is made. Status endpoints show `"status": "provisioning"` indefinitely.
- **provisioning-agent**: Registration workflows stall mid-execution.

**NOT affected:**

- **Postgres**: Continues serving reads. Previously committed data is intact.
- **Keycloak authentication**: Token issuance continues independently.
- **Web-console static assets**: Continue serving normally.
- **Vault**: Unaffected unless worker crash was triggered by Vault connectivity issues.

**Data loss risk**: None — Temporal workflow history is durable. When workers recover, they resume from the last successful activity checkpoint. No work is lost.

## Pre-Checks

```bash
# Check temporal-workers pod status
kubectl get pods -n dataspace-platform | grep temporal-workers

# Check recent worker logs for errors
kubectl logs deployment/temporal-workers -n dataspace-platform --tail=100 | grep -E "ERROR|FATAL|error"

# Check Temporal Server pod status
kubectl get pods -n temporal

# Check Temporal UI for task queue status (if accessible)
# Temporal UI: https://temporal.your-org.internal
```

## Communication Steps

| Time | Action | Channel | Audience |
|------|--------|---------|---------|
| Immediately | Acknowledge the alert | PagerDuty | On-call |
| +5 min | Post in `#platform-incidents`: "Temporal workers stalled — workflows not progressing" | Slack | Platform team |
| +10 min (if unresolved) | Page infra-lead | PagerDuty | infra-lead |
| +30 min | Notify stakeholders of delayed onboarding/export operations | Slack `#platform-status` | All stakeholders |

## Triage Checklist

1. [ ] Are temporal-workers pods running and ready? (`kubectl get pods -n dataspace-platform | grep temporal-workers`)
2. [ ] Are temporal-workers pods in `CrashLoopBackOff`? (different scenario from simple stall)
3. [ ] Is the Temporal Server reachable from the worker pods? (gRPC connectivity)
4. [ ] Is Vault reachable from the worker pods? (signing activities require Vault)
5. [ ] Is Postgres reachable from the worker pods? (DB activities require Postgres)
6. [ ] Was there a recent `temporal-workers` deployment that introduced a determinism error?

## Investigation Steps

### Step 1: Check worker pod status and recent restarts

```bash
kubectl get pods -n dataspace-platform -l app=temporal-workers -o wide

# If CrashLoopBackOff: check previous container logs
kubectl logs deployment/temporal-workers -n dataspace-platform --previous | tail -50
```

**If CrashLoopBackOff**: See Scenario A (worker crash loop).
**If Running but backlog high**: workers are connected but activities are failing. Proceed to Step 2.

### Step 2: Check worker logs for error patterns

```bash
kubectl logs deployment/temporal-workers -n dataspace-platform --tail=200 | grep -E "ERROR|error|exception|timeout|refused"
```

Common patterns:
- `vault: connection refused` or `vault: 403 Forbidden` → Vault connectivity issue (see Scenario B)
- `psycopg2.OperationalError: could not connect to server` → Postgres unavailable (see [Postgres Unavailable](postgres-unavailable.md))
- `NonDeterminismError: ...` → workflow code has a determinism bug (see Scenario C)
- `grpc._channel._InactiveRpcError: StatusCode.UNAVAILABLE` → Temporal Server unreachable (see Scenario D)

### Step 3: Check Temporal Server connectivity

```bash
# Check Temporal Server pods
kubectl get pods -n temporal

# Check Temporal gRPC from worker pod
kubectl exec -it deployment/temporal-workers -n dataspace-platform -- \
  python3 -c "import grpc; channel = grpc.insecure_channel('temporal-server.temporal.svc.cluster.local:7233'); stub = channel.channel_ready_future(); print('Connected')"
```

### Step 4: Check Temporal UI for stuck workflows

Navigate to the Temporal UI at `https://temporal.your-org.internal`. In the `dataspace` namespace:
- Filter by `Status: Running` to see all in-progress workflows
- Click into a stalled workflow to see the last event in the history
- Look at the last activity name and whether it has exceeded its retry count

### Step 5: Check if activities are failing or just not being scheduled

```bash
# Check Temporal task queue pollers — are workers registered?
kubectl exec -it deployment/temporal-workers -n dataspace-platform -- \
  temporal task-queue describe --task-queue dataspace-default --namespace dataspace 2>/dev/null || \
  echo "temporal CLI not available in worker container — check Temporal UI"
```

In Temporal UI: Go to Task Queues → `dataspace-default`. If Pollers = 0, workers are not connected to the task queue.

## Remediation / Rollback

### Scenario A: Worker crash loop

```bash
# Check what is causing the crash
kubectl logs deployment/temporal-workers -n dataspace-platform --previous | tail -100

# Common fix: if a dependency (Vault, Postgres) was unavailable on startup:
kubectl rollout restart deployment/temporal-workers -n dataspace-platform

# Watch the restart
kubectl rollout status deployment/temporal-workers -n dataspace-platform
```

If the crash loop continues after 3 restarts, the cause is likely a code bug or missing configuration. Do not keep restarting — investigate the logs.

### Scenario B: Vault connectivity blocking activities

Signing activities fail with 403 or connection refused. The workers themselves are running but cannot complete signing-dependent activities.

See [Vault Transit Failures](vault-transit-failures.md) for full remediation.

Quick check:
```bash
kubectl exec -it deployment/temporal-workers -n dataspace-platform -- \
  curl -sk https://vault.dataspace-infra.svc.cluster.local:8200/v1/sys/health | python3 -m json.tool
```

Expected: `{"sealed": false, ...}`. If 000 (connection refused): network policy blocking worker → Vault traffic. Check `infra/helm/charts/platform/templates/network-policies.yaml`.

### Scenario C: Determinism error in workflow code

```bash
# Find the workflow with the NonDeterminismError in Temporal UI
# Note the workflow ID and run ID

# Terminate the failing run (do NOT use cancel — terminate skips cleanup)
temporal workflow terminate \
  --workflow-id "<workflow-id>" \
  --reason "NonDeterminismError — developer investigation required" \
  --namespace dataspace

# The workflow will enter TERMINATED state. The entity (company, passport) remains in its last committed state in Postgres.
```

**After termination**: The affected entity needs manual state inspection. Check Postgres for the partial state, then re-submit the workflow via the control-api with a new idempotency key to restart.

**Root cause**: A recent code change to a workflow function introduced a non-deterministic operation (random, external API call, timestamp). Roll back the `temporal-workers` deployment:

```bash
kubectl rollout undo deployment/temporal-workers -n dataspace-platform
```

### Scenario D: Temporal Server unreachable

```bash
# Check Temporal Server pods
kubectl get pods -n temporal
kubectl describe pod temporal-frontend-0 -n temporal | tail -30

# Restart Temporal Server if crashing
kubectl rollout restart deployment/temporal-frontend -n temporal
kubectl rollout restart deployment/temporal-history -n temporal
kubectl rollout restart deployment/temporal-matching -n temporal
```

After Temporal Server recovers, the worker pods will automatically reconnect and resume processing the task queue. No manual worker restart needed.

## Evidence Capture Requirements

- [ ] List of workflow IDs that were in RUNNING state when the stall was detected (Temporal UI export)
- [ ] Worker pod logs from the stall window: `kubectl logs deployment/temporal-workers -n dataspace-platform --since=2h`
- [ ] Task queue backlog metric from Grafana at peak
- [ ] Count of workflows that failed permanently vs resumed after recovery

## Dashboards / Logs / Traces

| Resource | URL |
|---------|-----|
| Grafana — Temporal Dashboard | `https://grafana.your-org.internal/d/temporal-overview` |
| Temporal UI — running workflows | `https://temporal.your-org.internal/namespaces/dataspace/workflows?status=Running` |
| Loki — temporal-workers errors | `{namespace="dataspace-platform", app="temporal-workers"} \| json \| level="ERROR"` |
| Grafana — Task queue backlog | `https://grafana.your-org.internal/d/temporal-task-queues` |

## Escalation Contacts

| Role | Contact | Escalation trigger |
|------|---------|-------------------|
| infra-lead | `@infra-lead` PagerDuty | Not resolved in 10 min |
| procedures-lead | `@procedures-lead` Slack | NonDeterminismError or code-related crash |
| Platform lead | `@platform-lead` Slack | Not resolved in 30 min |

## Post-Incident Follow-Up

- [ ] Verify all stalled workflows resumed or were appropriately terminated
- [ ] Check whether any entities (companies, passports) are stuck in partial state due to terminated workflows
- [ ] If determinism error: ensure `tests/integration/replay/` suite is run before next procedure deployment
- [ ] Review worker resource limits if OOM was a contributing factor

## Related Runbooks

- [Vault Transit Failures](vault-transit-failures.md) — most common cause of activity-level worker stalls
- [Postgres Unavailable](postgres-unavailable.md) — second most common cause of DB activity failures
- [DPP Export Stuck](../procedures/dpp-export-stuck.md) — specific procedure runbook for DPP export workflows
