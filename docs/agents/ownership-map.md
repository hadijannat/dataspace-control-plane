---
title: "Ownership Map"
summary: "Top-level ownership boundaries, dependencies, and forbidden edit zones for the monorepo."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---
## Directory Owners

### `apps` owner

- Owned root path: `apps/`
- Upstream dependencies: `core/`, `procedures/`, `adapters/`, `packs/`, `schemas/`
- Downstream dependencies: `infra/`, `tests/`, `docs/`
- Forbidden edit zones: `core/`, `procedures/`, `adapters/`, `packs/`, `schemas/`, `infra/`, `tests/`, `docs/`
- Expected handoff outputs: changed runtime surfaces, API contract impact, workflow launch changes, generated-client impact, verification run, required downstream work

### `core` owner

- Owned root path: `core/`
- Upstream dependencies: `schemas/`, `docs/`
- Downstream dependencies: `procedures/`, `adapters/`, `apps/`, `tests/`, `packs/`
- Forbidden edit zones: `apps/`, `procedures/`, `adapters/`, `packs/`, `tests/`, `infra/`, `docs/`
- Expected handoff outputs: invariant changes, canonical model changes, new ports, audit implications, verification run, docs updates

### `procedures` owner

- Owned root path: `procedures/`
- Upstream dependencies: `core/`, `packs/`, `docs/`
- Downstream dependencies: `adapters/`, `apps/temporal-workers`, `tests/`, `docs/runbooks`
- Forbidden edit zones: `core/`, `adapters/`, `apps/`, `packs/`, `schemas/`, `infra/`, `docs/`
- Expected handoff outputs: workflow identity changes, phase/state updates, activity changes, replay/versioning notes, evidence outputs, required adapter work

### `adapters` owner

- Owned root path: `adapters/`
- Upstream dependencies: `core/`, `schemas/`, `packs/`
- Downstream dependencies: `procedures/`, `apps/`, `tests/`, `infra/`
- Forbidden edit zones: `core/`, `procedures/`, `apps/`, `packs/`, `schemas/`, `tests/`, `infra/`, `docs/`
- Expected handoff outputs: ports implemented, wire-model impact, readiness and health changes, secret handling notes, compatibility implications

### `packs` owner

- Owned root path: `packs/`
- Upstream dependencies: `core/`, `schemas/`, `docs/compliance-mappings`
- Downstream dependencies: `procedures/`, `apps/`, `tests/`, `docs/`
- Forbidden edit zones: `core/`, `procedures/`, `adapters/`, `apps/`, `schemas/`, `infra/`, `tests/`, `docs/`
- Expected handoff outputs: packs changed, effective-date or policy changes, normative assets pinned, conflicts resolved, required schema or procedure follow-up

### `schemas` owner

- Owned root path: `schemas/`
- Upstream dependencies: pinned upstream standards, `core/`, `packs/`
- Downstream dependencies: `adapters/`, `procedures/`, `apps/`, `tests/`, `docs/api`
- Forbidden edit zones: `core/`, `procedures/`, `adapters/`, `apps/`, `packs/`, `infra/`, `docs/`
- Expected handoff outputs: artifacts added or changed, provenance updates, validation changes, examples and negative examples, downstream compatibility notes

### `tests` owner

- Owned root path: `tests/`
- Upstream dependencies: every product root plus `infra/` for environments
- Downstream dependencies: release decisions, PR review, runbooks
- Forbidden edit zones: `apps/`, `core/`, `procedures/`, `adapters/`, `packs/`, `schemas/`, `infra/`, `docs/`
- Expected handoff outputs: suites changed, gates introduced, environments required, artifacts produced, failures or gaps left for owning directories

### `infra` owner

- Owned root path: `infra/`
- Upstream dependencies: `apps/`, `adapters/`, `tests/`, `docs/runbooks`
- Downstream dependencies: deployment environments, operator workflows, observability consumers
- Forbidden edit zones: `apps/`, `core/`, `procedures/`, `adapters/`, `packs/`, `schemas/`, `tests/`, `docs/`
- Expected handoff outputs: packaging changes, environment changes, secrets handling impact, observability changes, verification run, runbook updates

### `docs` owner

- Owned root path: `docs/`
- Upstream dependencies: every top-level code root
- Downstream dependencies: operators, reviewers, security, compliance, future agents
- Forbidden edit zones: `apps/`, `core/`, `procedures/`, `adapters/`, `packs/`, `schemas/`, `tests/`, `infra/`
- Expected handoff outputs: docs changed, source-of-truth inputs used, broken links fixed, review triggers, remaining documentation debt

## Boundary Rules

- Ownership is exclusive at the top-level root. No two specialists should edit the same root in the same task unless the prompt explicitly authorizes a coordinated cross-directory change.
- When a task needs a new port, schema, workflow hook, or runtime surface outside the owned root, record a dependency note instead of silently crossing the boundary.
- The lead or orchestrator is responsible for synthesis after specialist owners finish. Specialists optimize for clean local changes and explicit handoffs, not for cross-root improvisation.
