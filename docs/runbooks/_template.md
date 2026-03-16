---
title: "[Runbook Title — short noun phrase describing the scenario]"
summary: "[One sentence describing what this runbook covers]"
owner: "[owning lead — e.g., infra-lead]"
last_reviewed: "YYYY-MM-DD"
severity: "P1"  # P1 | P2 | P3 | P4
affected_services:
  - "[service name]"
  - "[service name]"
status: draft
---

## Trigger / Alert Source

- **Alert name**: `[AlertManager alert name or Grafana alert rule name]`
- **Alert condition**: `[metric and threshold that fires the alert]`
- **Manual trigger**: [Describe how an operator might manually discover this issue — e.g., "operator reports 401 errors on login"]
- **Typical symptom**: [What the on-call operator will see first]

## Scope and Blast Radius

**Affected services when this scenario occurs:**

- [Service 1]: [how it is affected]
- [Service 2]: [how it is affected]

**NOT affected** (services that continue to work):

- [Service N]: [why it is unaffected]

**Data loss risk**: [None / Low / Medium / High] — [brief explanation]

## Pre-Checks

Before starting the triage, verify the basics. These commands should take < 2 minutes.

```bash
# Check overall pod health in the platform namespace
kubectl get pods -n dataspace-platform

# Check infrastructure services
kubectl get pods -n dataspace-infra

# Check recent events for errors
kubectl get events -n dataspace-platform --sort-by='.lastTimestamp' | tail -20
```

## Communication Steps

| Time | Action | Channel | Audience |
|------|--------|---------|---------|
| Immediately | Acknowledge the alert | PagerDuty / Slack `#platform-incidents` | On-call team |
| +5 min (if not resolved) | Post incident status update | Slack `#platform-incidents` | Platform team |
| +10 min (if not resolved) | Page infra-lead | PagerDuty | infra-lead |
| +30 min (P1 only) | Notify stakeholders | Slack `#platform-status` | All stakeholders |

## Triage Checklist

1. [ ] Verify the alert is genuine (not a false alarm from a deployment or restart)
2. [ ] Identify the affected component(s)
3. [ ] Determine the scope: is this affecting all tenants or a specific tenant?
4. [ ] Check whether a recent deployment or change may have caused this
5. [ ] Check whether external dependencies (Vault, Keycloak, EDC) are contributing

## Investigation Steps

### Step 1: [Diagnostic step name]

```bash
# [Command with explanation]
<command>
```

**What to look for**: [What a healthy vs unhealthy output looks like]

**If you see X**: proceed to [step/remediation section]
**If you see Y**: this is a different issue — see [related runbook link]

### Step 2: [Next diagnostic step]

```bash
<command>
```

## Remediation / Rollback

!!! danger "Verify before acting"
    Confirm the diagnosis before executing remediation steps. Some steps have irreversible effects.

### Scenario A: [Most common root cause]

```bash
# Step 1: [description]
<command>

# Step 2: [description]
<command>
```

**Verify recovery**:

```bash
<verification command>
```

Expected output: `[what a recovered system looks like]`

### Scenario B: [Less common root cause]

[Steps for scenario B]

### Rollback

If the remediation makes things worse, roll back:

```bash
<rollback command>
```

## Evidence Capture Requirements

Before completing the incident, capture the following evidence for the post-incident report:

- [ ] `kubectl describe pod <pod-name> -n <namespace>` output saved to incident ticket
- [ ] Pod logs from the affected time window: `kubectl logs <pod> -n <namespace> --since=1h`
- [ ] Alert firing time and resolution time recorded
- [ ] Any Vault audit log entries relevant to the incident exported
- [ ] Screenshot of the Grafana dashboard at the time of the incident

## Dashboards / Logs / Traces

| Resource | URL |
|---------|-----|
| Grafana — Platform Overview | `https://grafana.your-org.internal/d/platform-overview` |
| Grafana — [Component] Dashboard | `https://grafana.your-org.internal/d/<dashboard-id>` |
| Loki — Platform logs | `https://grafana.your-org.internal/explore?orgId=1&datasource=loki` |
| Tempo — Distributed traces | `https://grafana.your-org.internal/explore?orgId=1&datasource=tempo` |
| Temporal UI | `https://temporal.your-org.internal` |
| Vault UI | `https://vault.your-org.internal` |

**Loki query for this incident**:

```logql
{namespace="dataspace-platform", app="<service>"} |= "error" | json | level="ERROR"
```

## Escalation Contacts

| Role | Contact | Escalation trigger |
|------|---------|-------------------|
| infra-lead | `@infra-lead` on Slack / PagerDuty | Not resolved in 10 min |
| DBA | `@dba-team` on Slack | Postgres data issue |
| Platform lead | `@platform-lead` on Slack | Not resolved in 30 min |

## Post-Incident Follow-Up

- [ ] Update this runbook if the triage steps were insufficient or incorrect
- [ ] File a post-incident report in the incident tracking system
- [ ] Create a backlog ticket for any infrastructure hardening identified
- [ ] Update `docs/arc42/11-risks-and-technical-debt.md` if a new risk was discovered
- [ ] Review whether the blast radius assumption in this runbook was accurate

## Related Runbooks

- [Postgres Unavailable](incidents/postgres-unavailable.md) — example of an infrastructure dependency incident
- [Vault Transit Failures](incidents/vault-transit-failures.md) — example of a signing-boundary incident
