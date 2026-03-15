---
title: "Postgres Unavailable"
summary: "Runbook for recovering from PostgreSQL pod crashes, OOM kills, storage exhaustion, and connection pool exhaustion."
owner: infra-lead
last_reviewed: "2026-03-14"
severity: "P1"
affected_services:
  - control-api
  - temporal-workers
  - provisioning-agent
status: approved
---

# Postgres Unavailable

## Trigger / Alert Source

- **Alert names**: `ControlApiDown`, `PostgresPodNotReady`, `PostgresConnectionRefused`
- **Alert conditions**: `up{job="postgres"} == 0` for > 2 minutes OR `kube_pod_status_ready{namespace="dataspace-infra",pod=~"postgres-.*"} == 0`
- **Manual trigger**: Operators report that API mutations are failing with 503 errors; Temporal workflow activities are failing with database connection errors
- **Typical symptom**: Grafana `Platform Overview` dashboard shows red pod status for `postgres-0`; Temporal UI shows multiple workflows in `RUNNING` state with no activity completions

## Scope and Blast Radius

**Affected when Postgres is unavailable:**

- **control-api**: All write operations fail (`POST /companies`, `POST /passports`, etc.). Read operations may partially work if the read replica is available.
- **temporal-workers**: All activities that write to Postgres fail with connection errors. Workflows stall in RUNNING state until Postgres recovers (Temporal retries activities automatically).
- **provisioning-agent**: Company onboarding fails at the tenant record creation step.

**NOT affected** (services that continue to work):

- **web-console**: Static assets serve normally. API calls will fail but the UI remains up.
- **Keycloak**: Uses a separate PostgreSQL instance (`dataspace-infra/keycloak-postgres`).
- **Vault**: Fully independent of the platform Postgres.
- **Temporal Server**: Uses its own Postgres (`temporal/temporal-postgres`).

**Data loss risk**: Low — Temporal activities retry automatically. Any transaction that was in-flight during the crash will be rolled back by Postgres on recovery. Temporal retry ensures the activity re-executes cleanly.

## Pre-Checks

```bash
# Check Postgres pod status
kubectl get pods -n dataspace-infra | grep postgres

# Check recent pod events
kubectl describe pod postgres-0 -n dataspace-infra | tail -30

# Check recent pod logs
kubectl logs postgres-0 -n dataspace-infra --tail=50

# Check PVC status (storage issues show here)
kubectl get pvc -n dataspace-infra | grep postgres
```

## Communication Steps

| Time | Action | Channel | Audience |
|------|--------|---------|---------|
| Immediately | Acknowledge the alert | PagerDuty | On-call |
| +2 min | Post in `#platform-incidents`: "Postgres down — investigating" | Slack | Platform team |
| +10 min (if unresolved) | Page infra-lead | PagerDuty | infra-lead |
| +15 min (if unresolved) | Page DBA on-call | PagerDuty | DBA team |
| +30 min | Notify stakeholders that API writes are degraded | Slack `#platform-status` | All stakeholders |

## Triage Checklist

1. [ ] Is the pod crashing or just slow to start? Check `kubectl get pods -n dataspace-infra` for `CrashLoopBackOff` vs `Pending` vs `Terminating`
2. [ ] Is this a single pod failure (replica down) or all Postgres pods down?
3. [ ] Was there a recent deployment, PVC resize, or node maintenance that could have caused this?
4. [ ] Is this affecting all tenants or only tenants whose queries hit a specific Postgres partition?
5. [ ] Is Temporal reporting workflow failures, or are workflows merely paused waiting for activities?

## Investigation Steps

### Step 1: Check pod crash reason

```bash
kubectl describe pod postgres-0 -n dataspace-infra
```

Look for:
- `OOMKilled` in `Last State.Reason` → memory limit too low; see Scenario A
- `Error` exit code in `Last State` → Postgres FATAL error; check logs
- `Evicted` → node pressure; check node resources: `kubectl describe node <node-name>`

### Step 2: Check Postgres logs for FATAL errors

```bash
kubectl logs postgres-0 -n dataspace-infra --tail=100 | grep -E "FATAL|ERROR|PANIC"
```

Common FATALs:
- `FATAL: could not open file "pg_wal/..."` → WAL corruption; see Scenario C
- `FATAL: the database system identifier differs` → PVC was swapped; contact DBA immediately
- `FATAL: out of memory` → shared_buffers or work_mem too high; see Scenario A

### Step 3: Check storage utilization

```bash
kubectl exec -it postgres-0 -n dataspace-infra -- df -h /var/lib/postgresql/data
```

If usage > 90%, storage is full. See Scenario B.

### Step 4: Check PostgreSQL is in recovery mode

```bash
kubectl exec -it postgres-0 -n dataspace-infra -- \
  psql -U dataspace -c "SELECT pg_is_in_recovery();"
```

Expected on primary: `f` (false). If `t` (true) on the primary, the primary is running as a replica — contact DBA.

### Step 5: Check connection pool exhaustion in control-api

```bash
# Check how many connections Postgres is accepting
kubectl exec -it postgres-0 -n dataspace-infra -- \
  psql -U dataspace -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check max connections setting
kubectl exec -it postgres-0 -n dataspace-infra -- \
  psql -U dataspace -c "SHOW max_connections;"
```

If `count(*)` of `active` connections equals `max_connections`, the pool is exhausted. See Scenario D.

## Remediation / Rollback

### Scenario A: OOMKilled (pod killed by Kubernetes OOM killer)

```bash
# Patch the Postgres StatefulSet to increase memory limits
kubectl patch statefulset postgres -n dataspace-infra \
  --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"6Gi"}]'

# Restart the pod to apply new limits
kubectl rollout restart statefulset/postgres -n dataspace-infra

# Watch the rollout
kubectl rollout status statefulset/postgres -n dataspace-infra
```

**Verify recovery**: `kubectl exec -it postgres-0 -n dataspace-infra -- psql -U dataspace -c "SELECT 1;"`

**Follow-up**: Update the Postgres `resources.limits.memory` value in `infra/helm/charts/platform/values.yaml` and re-apply via Helm.

### Scenario B: Storage full (PVC at 90%+ capacity)

```bash
# Expand the PVC (requires StorageClass to support volume expansion)
kubectl patch pvc postgres-data-postgres-0 -n dataspace-infra \
  --type=json \
  -p='[{"op":"replace","path":"/spec/resources/requests/storage","value":"100Gi"}]'

# Verify the PVC expansion is accepted
kubectl get pvc postgres-data-postgres-0 -n dataspace-infra

# If immediate relief needed: clean up old WAL files (only if confirmed safe by DBA)
kubectl exec -it postgres-0 -n dataspace-infra -- \
  psql -U dataspace -c "SELECT pg_switch_wal();"
```

**Follow-up**: Update PVC size in Terraform (`infra/terraform/roots/platform/postgres.tf`) and plan for data archival.

### Scenario C: CrashLoopBackOff (non-OOM)

```bash
# Get the last few lines before crash
kubectl logs postgres-0 -n dataspace-infra --previous | tail -30

# If logs suggest normal startup: just wait and observe
# Postgres sometimes crashes during WAL recovery on startup — it retries automatically
kubectl get pods -n dataspace-infra -w
```

If the pod keeps crashing after 5 attempts: contact the DBA team and do not attempt manual Postgres file repairs without DBA guidance.

### Scenario D: Connection pool exhausted

```bash
# Restart control-api pods to reset connection pools (safe — Temporal will retry stalled activities)
kubectl rollout restart deployment/control-api -n dataspace-platform

# Restart temporal-workers to reset their connection pools
kubectl rollout restart deployment/temporal-workers -n dataspace-platform

# Verify pool cleared
kubectl exec -it postgres-0 -n dataspace-infra -- \
  psql -U dataspace -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
```

## Evidence Capture Requirements

Before closing the incident:

- [ ] `kubectl describe pod postgres-0 -n dataspace-infra` → saved to incident ticket
- [ ] `kubectl logs postgres-0 -n dataspace-infra --since=2h` → saved to incident ticket
- [ ] Storage utilization at time of incident: `df -h` output from pod
- [ ] Connection count at peak: `pg_stat_activity` query output
- [ ] Time of alert, time of first responder acknowledgement, time of recovery

## Dashboards / Logs / Traces

| Resource | URL |
|---------|-----|
| Grafana — Postgres Dashboard | `https://grafana.your-org.internal/d/postgres-overview` |
| Grafana — Platform Overview | `https://grafana.your-org.internal/d/platform-overview` |
| Loki — Postgres logs | `{namespace="dataspace-infra", app="postgres"}` |
| Loki — control-api DB errors | `{namespace="dataspace-platform", app="control-api"} |= "db" |= "error"` |

## Escalation Contacts

| Role | Contact | Escalation trigger |
|------|---------|-------------------|
| infra-lead | `@infra-lead` PagerDuty | Not resolved in 10 min |
| DBA team | `@dba-oncall` PagerDuty | WAL corruption, data loss risk, or storage issue |
| Platform lead | `@platform-lead` Slack | Not resolved in 30 min |

## Post-Incident Follow-Up

- [ ] Update Postgres memory/storage limits in Helm chart if Scenario A or B
- [ ] Review connection pool settings in `apps/control-api/config/database.py`
- [ ] Check whether Temporal activities failed permanently (FAILED state) vs retried successfully
- [ ] Update risk R-05 in `docs/arc42/11-risks-and-technical-debt.md` if a new failure mode was discovered

## Related Runbooks

- [Temporal Workers Stalled](temporal-workers-stalled.md) — Postgres outage often causes Temporal activity failures
- [Vault Transit Failures](vault-transit-failures.md) — concurrent issue in rare multi-component failure scenarios
