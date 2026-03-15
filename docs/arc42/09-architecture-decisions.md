---
title: "9. Architecture Decisions"
summary: "Index of all MADR architecture decision records with status, date, affected layers, and prose summaries of the most load-bearing decisions."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# 9. Architecture Decisions

Architecture decisions are recorded as MADR (Markdown Architectural Decision Records) in `docs/adr/`. This section provides the index and prose context for the most load-bearing decisions.

## ADR Index

| ADR | Title | Status | Date | Affected layers | Decision-makers |
|-----|-------|--------|------|----------------|----------------|
| [0001](../adr/0001-use-mkdocs-material.md) | Use MkDocs + Material for documentation | Accepted | 2026-03-14 | `docs/` | docs-lead |
| [0002](../adr/0002-adopt-temporal-as-workflow-engine.md) | Adopt Temporal as the workflow engine | Accepted | 2026-03-14 | `procedures/`, `apps/`, `tests/` | docs-lead, all leads |
| [0003](../adr/0003-json-schema-2020-12-as-house-dialect.md) | JSON Schema 2020-12 as the house dialect | Accepted | 2026-03-14 | `schemas/`, `adapters/`, `packs/` | schemas-lead, all leads |
| [0004](../adr/0004-vault-transit-for-signing-keys.md) | Vault Transit for all signing operations | Accepted | 2026-03-14 | `procedures/`, `adapters/`, `tests/` | infra-lead, all leads |
| [0005](../adr/0005-packs-as-pure-overlay.md) | Packs as pure overlays over core | Accepted | 2026-03-14 | `packs/`, `core/` | packs-lead, core-lead |

## Prose Context for Load-Bearing Decisions

### ADR 0002 — Temporal as the Workflow Engine

Temporal was chosen over alternatives (Conductor, Celery, custom outbox) specifically because of `WorkflowEnvironment.start_time_skipping()`, which enables deterministic, unit-speed testing of time-sensitive business processes such as certificate expiry windows, metering settlement intervals, and ODRL policy time-bound permissions. Without replay-safe deterministic testing, every multi-step procedure would require integration test environments with real clock advances. Temporal also eliminates the need for compensating transaction logic in application code: if an activity fails, Temporal retries it with the configured retry policy. The workflow history is the audit trail.

### ADR 0004 — Vault Transit for All Signing Operations

The Vault Transit decision has the highest blast-radius risk of all ADRs: if it were reversed, private key material would need to be managed in application code or Postgres, creating a much larger attack surface for the tamper-evident evidence trail. Vault Transit keys are created with `exportable=false` and `allow_plaintext_backup=false`. The Vault audit log records every signing request (key ID, caller identity, timestamp) without exposing the key material. Key rotation is non-disruptive: Vault key versioning allows the platform to rotate to a new key version while the old version remains valid for verification of previously signed artifacts during the rotation window.

### ADR 0005 — Packs as Pure Overlays

The pack overlay model is what makes multi-regulation deployment possible without forking `core/`. The Battery Passport regulation requires Annex XIII field tiers; ESPR requires different field completeness checks; Catena-X requires ODRL policy profile validation. If these rules were embedded in `core/` or `adapters/`, adding a new regulation would require modifying layers that other packs and procedures depend on. The pure overlay model means each pack is a composable unit: a `PassportExportWorkflow` can simultaneously apply `battery_passport`, `espr_dpp`, and `catenax` packs by invoking the `PackReducer` with all three. Conflicts between pack rules are declared explicitly in the reducer, not silently suppressed.

## How to Add a New ADR

1. Copy `docs/adr/_template.md` to `docs/adr/NNNN-short-slug.md`.
2. Fill in all front matter fields: status, date, decision-makers, consulted, informed.
3. Complete all body sections: Context, Decision Drivers, Options, Outcome, Consequences.
4. Add the ADR to the index table in this file and in `docs/adr/index.md`.
5. Link the ADR from the relevant arc42 section (Section 2 if it addresses a constraint, Section 4 if it is a solution strategy bet, Section 8 if it governs a crosscutting concept).
6. Set `status: proposed` initially; change to `accepted` after team review in the relevant wave review (`/review-wave`).
