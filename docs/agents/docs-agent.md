---
title: "Docs Agent Guidebook"
summary: "Deep guidebook for the docs owner, including site, governance, and docs-family responsibilities."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---
## Purpose

- Own `docs/` as the curated explanation and governance layer. Documentation explains and governs the system; it does not mirror code one-to-one.

## Scope

- Maintain architecture narratives, ADRs, API references, runbooks, threat models, compliance mappings, and agent guidebooks.
- Keep sources of truth explicit and cross-links current.
- Distinguish hand-written explanation from generated reference material.

## Owned Paths

- `docs/adr`
- `docs/arc42`
- `docs/api`
- `docs/runbooks`
- `docs/threat-model`
- `docs/compliance-mappings`
- `docs/agents`

## Explicitly Non-Owned Paths

- `apps/`
- `core/`
- `procedures/`
- `adapters/`
- `packs/`
- `schemas/`
- `tests/`
- `infra/`

## What This Agent Must Read First

1. `docs/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for broad docs or governance updates
5. The owning guidebook for any product root whose behavior is being documented

## Architecture Invariants

- `docs/` is curated explanation, not a mirror of the source tree.
- Docs-as-code rules apply: documents are versioned, reviewable, and linked to owning directories.
- Generated reference docs and hand-written guidance must be clearly separated.
- The repository-root `mkdocs.yml` is the canonical docs site configuration.
- Docs Node tooling lives in `docs/package.json`; docs Python tooling lives in
  `docs/requirements.txt`.
- Every architecture, interface, workflow, trust-boundary, or compliance change must trigger doc review.

## Subdirectory-By-Subdirectory Responsibilities

### `docs/adr`

- Purpose: record durable architectural decisions and tradeoffs
- Source of truth: reviewed decision records authored by humans or agents with explicit context
- Generation or authoring process: hand-written markdown, updated when decisions are made or revised
- Review or update triggers: architecture boundary changes, protocol choices, runtime strategy changes, verification strategy changes

### `docs/arc42`

- Purpose: maintain system architecture explanations for the whole monorepo
- Source of truth: curated architectural narratives synthesized from code and ADRs
- Generation or authoring process: hand-written or partially generated summaries, but always reviewed for architectural accuracy
- Review or update triggers: changes to layer boundaries, deployment topology, integration strategy, or operator workflows

### `docs/api`

- Purpose: document API contracts, public surfaces, webhook semantics, and machine-consumable interface expectations
- Source of truth: generated specs where available plus hand-written explanatory notes
- Generation or authoring process: generated artifacts should be clearly marked; explanatory markdown stays hand-written
- Review or update triggers: any change in request or response shape, auth model, stream contract, or compatibility profile

### `docs/runbooks`

- Purpose: document operational workflows, incident handling, recovery steps, and deployment procedures
- Source of truth: operational behavior implemented in apps, procedures, adapters, and infra
- Generation or authoring process: hand-written and kept aligned to real operational flows
- Review or update triggers: alert changes, workflow changes, deployment changes, new failure modes, evidence export changes

### `docs/threat-model`

- Purpose: describe trust boundaries, attack surfaces, sensitive flows, and mitigations
- Source of truth: synthesized from architecture, machine-trust flows, infra, adapters, and procedures
- Generation or authoring process: hand-written or security-review-driven markdown with references to code and ADRs
- Review or update triggers: credential flow changes, tenancy changes, connector exposure changes, new external integrations

### `docs/compliance-mappings`

- Purpose: map regulations, ecosystem requirements, and evidence obligations to packs, procedures, schemas, and runtime surfaces
- Source of truth: pack definitions, compliance semantics in `core/`, schema bundles, and operator procedures
- Generation or authoring process: curated markdown with linked artifacts and evidence references
- Review or update triggers: regulatory changes, pack revisions, DPP requirement updates, new evidence flows

### `docs/agents`

- Purpose: hold agent routing playbooks, ownership rules, and orchestration guidance
- Source of truth: this guidance scaffold and future refinements to repo governance
- Generation or authoring process: hand-written markdown, with template support from `_template.md`
- Review or update triggers: ownership changes, new top-level roots, planning changes, skill additions, or orchestration model changes

## Allowed Dependencies

- Every product root as an input source of truth
- `PLANS.md` and `AGENTS.md` files as governance inputs
- Generated contract artifacts where clearly marked

## Forbidden Shortcuts

- Do not copy code into docs as a substitute for explanation.
- Do not leave generated API docs unlabeled and mixed with hand-written guidance.
- Do not update narrative docs without checking the actual owning layer.
- Do not let runbooks drift from operational reality because a code owner skipped docs follow-up.
- Do not create a docs site config outside `docs/` when one is eventually added.

## Build / Implementation Order

1. Identify the owning product root and source-of-truth files.
2. Update the narrowest affected document family first.
3. Propagate changes to architecture, runbook, compliance, or threat-model docs as needed.
4. Repair cross-links between guidebooks, AGENTS files, and related docs.
5. Add follow-up notes for any missing source-of-truth updates outside `docs/`.

## Required Tests / Verification

- Existing structural checks:
  - `find docs -maxdepth 2 -type d | sort`
  - `test -f docs/AGENTS.md`
  - `test -f docs/agents/docs-agent.md`
- Required command: `make test-docs`
- Required command: `pnpm --dir docs exec markdownlint-cli2 "**/*.md"`
- Required command: `pytest tests/unit/docs -q`

## Required Docs Updates

- Update the relevant document family whenever architecture, interfaces, procedures, trust boundaries, or compliance requirements change.
- Update guidebooks and local `AGENTS.md` files when ownership or verification rules change.
- Record unresolved documentation debt explicitly in handoffs when source-of-truth code changed but docs work could not be completed.

## Common Failure Modes

- Docs mirror code layout without explaining why the system is shaped that way.
- Runbooks lag behind actual alerting or recovery behavior.
- Threat-model docs ignore new trust or tenancy edges.
- Compliance mappings lag pack or DPP changes.
- Guidebooks become stale after ownership shifts.

## Handoff Contract

- Report which doc families changed and why.
- Name the source-of-truth inputs consulted.
- Note generated versus hand-written boundaries touched.
- Report cross-links fixed, verification run, and remaining doc debt.
- Leave follow-up notes for code owners when docs exposed missing source-of-truth updates.

## Done Criteria

- Docs remain curated and source-of-truth aware.
- Architecture, API, runbook, threat-model, and compliance updates are aligned to actual system changes.
- Generated and hand-written documentation boundaries are explicit.
- Guidebooks, local `AGENTS.md`, and governance docs stay consistent.

## Example Prompts For This Agent

- "Update `docs/runbooks` and `docs/api` for a new operator webhook flow in the control API."
- "Refresh `docs/compliance-mappings` after a battery-passport pack revision changes required evidence."
- "Revise the guidebooks in `docs/agents` after adding a new top-level owner or changing verification rules."
