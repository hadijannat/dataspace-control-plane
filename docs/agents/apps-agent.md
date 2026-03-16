---
title: "Apps Agent Guidebook"
summary: "Deep guidebook for the apps owner, including runtime-surface boundaries and handoff expectations."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---
## Purpose

- Own runtime entrypoints in `apps/` and keep them thin, compositional, and bounded by contracts from `core/`, `procedures/`, `adapters/`, `packs/`, and `schemas/`.

## Scope

- Implement user-facing and runtime-facing application surfaces.
- Register durable workflows and activities in runtime containers.
- Expose operator and public APIs without redefining domain meaning.
- Keep provisioning and EDC runtime glue operational, not semantic.

## Owned Paths

- `apps/web-console`
- `apps/control-api`
- `apps/temporal-workers`
- `apps/edc-extension`
- `apps/provisioning-agent`

## Explicitly Non-Owned Paths

- `core/`
- `procedures/`
- `adapters/`
- `packs/`
- `schemas/`
- `tests/`
- `infra/`
- `docs/`

## What This Agent Must Read First

1. `apps/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for any cross-directory work
5. Relevant procedure and adapter contracts before changing app boundaries

## Architecture Invariants

- `apps/` owns runtime entrypoints and user interfaces, not canonical domain meaning.
- `apps/web-console` is a React operator console and must talk to `apps/control-api`, not to adapters directly.
- `apps/control-api` is the human-facing and public backend surface. Long-running mutations must start workflows rather than do inline orchestration.
- `apps/temporal-workers` hosts durable execution runtime. It registers workflows and activities but must not redefine business semantics from `core/` or `procedures/`.
- `apps/edc-extension` is only for code that must run inside an EDC runtime. Keep it thin and runtime-specific.
- `apps/provisioning-agent` reconciles declarative bootstrap state. It must not become an alternative orchestration engine.
- Browser code must never hold machine-trust private material, long-lived operator secrets, or wallet signing material.

## Subdirectory-By-Subdirectory Responsibilities

### `apps/web-console`

- Render the operator console shell, workflow dashboards, policy composition UI, and environment status views.
- Consume generated clients or shared API contracts from `apps/control-api`.
- Hold operator IAM session state only; no machine-trust keys, connector client secrets, or workflow secrets.
- Surface workflow state, pack selection, compliance gaps, and evidence status without reimplementing policy translation or schema validation.

### `apps/control-api`

- Expose operator API, public API, stream endpoints, and webhook ingestion as distinct surfaces.
- Validate requests, authorize operators, and translate requests into procedure launches or domain service calls.
- Treat workflow-start endpoints as coordination boundaries: accept intent, persist request metadata if needed, then hand off to procedures or workers.
- Keep router code thin. Domain logic belongs in `core/`; orchestration logic belongs in `procedures/`.

### `apps/temporal-workers`

- Register workflow and activity implementations for procedure packages.
- Configure task queues, worker identity, retries, heartbeat, and telemetry integration.
- Keep workflow code deterministic and activity code idempotent or compensatable.
- Use workflow state for business progress only; external clients, raw secrets, and huge payloads stay in activities or adapter stores.

### `apps/edc-extension`

- Host connector-runtime hooks that must execute inside EDC extension points.
- Bridge thin runtime-specific behavior to adapter or core contracts without re-encoding business rules.
- Keep deployability and runtime compatibility explicit because EDC upgrades can be frequent and breaking.

### `apps/provisioning-agent`

- Reconcile desired state for connector bootstrap, wallet bootstrap, and environment setup.
- Act as a declarative bootstrap tool, not as a long-running business process engine.
- Call out to procedures when business sequencing, approvals, or durable evidence matter.

## Allowed Dependencies

- `core/` for canonical models, operator access rules, tenant topology, machine trust, policies, contracts, audit contracts
- `procedures/` for workflow names, start inputs, status shapes, and human review points
- `adapters/` indirectly through workers and runtime composition, not through browser code
- `packs/` for available ecosystem or regulatory overlays presented to operators
- `schemas/` for generated clients, request and response contracts, and artifact validation boundaries
- `tests/` for integration, e2e, compatibility, tenancy, and replay coverage
- `infra/` for packaging and deployment contracts
- `docs/` for runbooks, API docs, and architecture references

## Forbidden Shortcuts

- Do not put domain logic in FastAPI routers or HTTP handlers.
- Do not let the React console call adapters or databases directly.
- Do not store machine-trust keys, wallet secrets, or connector secrets in browser state.
- Do not write workflow logic inside `apps/provisioning-agent`.
- Do not fork canonical models in EDC extension code to satisfy runtime quirks.
- Do not create handwritten fetch layers when a generated control API client should exist.

## Build / Implementation Order

1. Confirm required core contracts, procedure identities, and adapter ports exist. If not, stop at the boundary and record dependency notes.
2. Stabilize `apps/control-api` request and response contracts first.
3. Register or wire `apps/temporal-workers` to the relevant procedure packages and activities.
4. Add `apps/edc-extension` only for runtime-only connector hooks that cannot live elsewhere.
5. Add or update `apps/provisioning-agent` for declarative bootstrap and reconcile flows.
6. Build `apps/web-console` last against stable generated API clients and workflow status surfaces.

## Required Tests / Verification

- Existing structural checks:
  - `find apps -maxdepth 2 -type d | sort`
  - `test -f apps/AGENTS.md`
  - `test -f docs/agents/apps-agent.md`
- Expected command once scaffolded: `make test-apps`
- Expected command once scaffolded: `pytest tests/integration -k apps`
- Expected command once scaffolded: `pytest tests/e2e -k web_console`
- Expected command once scaffolded: `pytest tests/tenancy -k operator_access`

## Required Docs Updates

- Update `docs/api/` when request, response, webhook, or stream contracts change.
- Update `docs/runbooks/` when operator workflow steps, alert handling, or recovery flow changes.
- Update `docs/arc42/` when runtime boundaries or deployment shape changes.
- Update `docs/agents/apps-agent.md` and local `apps/AGENTS.md` if ownership or runtime rules change.

## Common Failure Modes

- UI starts talking directly to adapters because an API surface was missing.
- FastAPI handlers accumulate orchestration logic and bypass durable workflows.
- Workflow registrations drift from procedure definitions.
- EDC extension code becomes a second adapter layer with copied semantics.
- Provisioning flows grow manual retry state instead of using proper procedures.
- Operator UI accidentally exposes machine-trust material or assumes connector-local state.

## Handoff Contract

- Report which app surfaces changed.
- Identify any new or changed workflow start points.
- List generated clients or API contracts that changed.
- State which verification steps ran and what remains expected but unimplemented.
- Record required follow-up in `core/`, `procedures/`, `adapters/`, `infra/`, or `docs/`.

## Done Criteria

- App code only composes existing meaning; it does not redefine it.
- Long-running mutations route into procedures and workers.
- Browser code holds no machine-trust private material.
- EDC extension code is thin and runtime-bound.
- Provisioning remains declarative and non-orchestration-centric.
- Docs and runbooks are updated for any changed surface.

## Example Prompts For This Agent

- "Add an operator endpoint in `apps/control-api` that starts the tenant delegation workflow and document the webhook contract."
- "Wire `apps/temporal-workers` to a new `procedures/evidence-export` workflow without moving business rules out of `procedures/`."
- "Extend `apps/web-console` to show DPP compliance gaps using the generated control API client."
