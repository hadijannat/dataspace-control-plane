---
title: "Runbooks"
summary: "Index of all operational runbooks for the dataspace control plane — incidents, platform procedures, workflow procedures, and external dependency issues."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

Runbooks provide step-by-step guidance for operating, diagnosing, and recovering the Dataspace Control Plane. Each runbook corresponds to a specific operational scenario: a type of incident, a platform maintenance procedure, a procedure-layer workflow failure, or an external dependency misconfiguration.

## Categories

| Category | Description |
|----------|-------------|
| **Incidents** | Reactive runbooks triggered by alerts or operator reports of service degradation. Includes triage, investigation, and remediation steps. |
| **Platform** | Proactive maintenance procedures: key rotation, certificate renewal, schema migration. Run on a schedule or when triggered by planned changes. |
| **Procedures** | Runbooks for failures in Temporal workflow execution — specific to the business process workflows in `procedures/`. |
| **External Dependencies** | Runbooks for issues in external systems (Keycloak, EDC connectors, DPP registry) that impact platform operation. |

## Runbook Index

### Incidents

| Runbook | Severity | Trigger |
|---------|---------|---------|
| [Postgres Unavailable](incidents/postgres-unavailable.md) | P1 | Postgres pod not ready; all API writes failing |
| [Vault Transit Failures](incidents/vault-transit-failures.md) | P1 | Signing operations returning 403 or timeout |
| [Temporal Workers Stalled](incidents/temporal-workers-stalled.md) | P1 | No workflow completions in >5 min; task queue backlog alert |

### Platform

| Runbook | Frequency | Description |
|---------|-----------|-------------|
| [Vault Key Rotation](platform/vault-key-rotation.md) | Quarterly or on compromise | Rotate Transit signing keys with zero-downtime key version window |
| [Certificate Renewal](platform/certificate-renewal.md) | 30 days before expiry (auto via cert-manager) | Manual certificate renewal if cert-manager auto-renewal fails |
| [Schema Migration](platform/schema-migration.md) | On schema change | Classify, version, and migrate JSON Schema changes with CI gate |

### Procedures

| Runbook | Trigger |
|---------|---------|
| [Connector Registration Failed](procedures/connector-registration-failed.md) | provisioning-agent alert; EDC connector not registered |
| [DPP Export Stuck](procedures/dpp-export-stuck.md) | DPP export workflow stuck in RUNNING > 30 min |

### External Dependencies

| Runbook | Trigger |
|---------|---------|
| [Keycloak Realm Misconfigured](external-dependencies/keycloak-realm-misconfigured.md) | 401 errors on all API calls; operators unable to log in |

## Template

All runbooks use the [runbook template](_template.md). The template enforces required sections: trigger, scope/blast radius, pre-checks, communication, triage, investigation, remediation, evidence capture, dashboards, escalation, and post-incident follow-up.

## Review Cadence

- **P1 runbooks**: reviewed quarterly. Must have `last_reviewed` within 90 days or are flagged as stale.
- **P2 runbooks**: reviewed semi-annually.
- **Platform and procedure runbooks**: reviewed after each relevant system change.

The quarterly review is run by infra-lead and docs-lead during the Wave 3 review session.

## Escalation Path

| Time in incident | Action |
|-----------------|--------|
| 0–5 min | First responder investigates using the runbook |
| 5–10 min | Notify `#platform-incidents` Slack channel |
| 10–30 min | If not resolved: page infra-lead (PagerDuty) |
| 30+ min | If not resolved: escalate to platform lead and DBA |
| 60+ min (P1) | Executive notification; incident commander assigned |
