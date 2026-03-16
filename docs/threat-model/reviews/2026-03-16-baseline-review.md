---
title: "Threat Model Baseline Review 2026-03-16"
summary: "Baseline review note covering the five maintained Threat Dragon models, open threats, and immediate follow-up actions."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

This review establishes the initial docs-as-code baseline for the threat-model
workspace.

## Scope Reviewed

- `platform.json`
- `onboarding.json`
- `negotiation.json`
- `dpp-provisioning.json`
- `machine-trust.json`

## Findings

- The platform-wide STRIDE model remains the canonical overview of trust
  boundaries across `control-api`, Temporal workers, Vault, Keycloak, Postgres,
  and external connectors.
- The onboarding and negotiation models still capture the most exposed
  workflow-level boundaries.
- Two focused models were added in this review cycle:
  - DPP provisioning, covering AAS and registry submission paths
  - machine trust, covering service tokens, stream tickets, and webhook
    authenticity
- One platform threat remains open: ODRL policy payload tampering during
  negotiation parsing.

## Follow-Up

- Keep the ODRL tampering threat linked to the relevant backlog item and
  `docs/arc42/11-risks-and-technical-debt.md`.
- Refresh rendered diagrams whenever the Threat Dragon JSON changes.
- Re-run this review before the next production release and after any change to
  trust boundaries or credential flows.
