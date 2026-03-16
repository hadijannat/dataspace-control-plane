---
title: "Infra Agent Guidebook"
summary: "Deep guidebook for the infra owner, including delivery-substrate responsibilities and runbook triggers."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---
## Purpose

- Own `infra/` as the delivery and runtime substrate. This layer packages, provisions, composes, and observes the system without taking over business logic.

## Scope

- Package releases in Helm.
- Provision durable shared infrastructure in Terraform.
- Define image builds and local composition in Docker.
- Define telemetry pipelines, dashboards, alerts, and rules in observability assets.

## Owned Paths

- `infra/helm`
- `infra/terraform`
- `infra/docker`
- `infra/observability`

## Explicitly Non-Owned Paths

- `apps/`
- `core/`
- `procedures/`
- `adapters/`
- `packs/`
- `schemas/`
- `tests/`
- `docs/`

## What This Agent Must Read First

1. `infra/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for environment, release, or observability changes
5. Relevant app and adapter guidebooks before changing runtime assumptions

## Architecture Invariants

- `helm/` owns release packaging only: charts, values, schemas, templates, and release wiring.
- `terraform/` owns shared durable infrastructure: root modules, reusable modules, state boundaries, and environment composition.
- `docker/` owns image builds and local composition; it does not define production orchestration policy.
- `observability/` owns telemetry pipelines, dashboards, alerts, SLO or rule definitions, and operator-facing telemetry assets.
- Infra does not define business workflows, canonical models, or adapter semantics.
- Secrets stay external to the repo and are referenced through environment or secret-management integration.
- Image releases should be immutable and reproducible.

## Subdirectory-By-Subdirectory Responsibilities

### `infra/helm`

- Purpose: package deployable releases for runtime components
- Owns: chart layout, values files, chart schemas, templates, chart tests once scaffolded
- Must not own: business defaults that belong in apps or core, environment-specific secrets, ad hoc operational scripts
- Handoff to others: expose required values, resource contracts, deployment assumptions, and upgrade notes to `docs/runbooks` and app owners

### `infra/terraform`

- Purpose: provision shared durable infrastructure and environment composition
- Owns: root modules, reusable modules, providers, state boundaries, remote-state references once defined
- Must not own: application business logic, ad hoc per-developer scripts disguised as infrastructure, runtime secrets committed to git
- Handoff to others: communicate outputs, environment assumptions, drift expectations, and bootstrap prerequisites to app, adapter, and docs owners

### `infra/docker`

- Purpose: build images and define local composition for development and integration
- Owns: Dockerfiles, build contexts, local compose definitions once scaffolded, image tag conventions
- Must not own: production scheduling policy, runtime business flags that belong to app config, cloud-specific infrastructure
- Handoff to others: document image contracts, build args, local stack assumptions, and artifact naming to tests and docs owners

### `infra/observability`

- Purpose: define telemetry pipelines, dashboards, alerting, and rules for runtime visibility
- Owns: collector configs, dashboards, alert rules, SLO support assets, telemetry routing
- Must not own: business event definitions from `core/`, ad hoc app logging semantics, one-off debug tooling committed as production config
- Handoff to others: communicate alert semantics, runbook links, dashboards, and required app instrumentation to app, adapter, tests, and docs owners

## Allowed Dependencies

- `apps/` for deployable surfaces and runtime config contracts
- `adapters/` for connector, trust, persistence, and telemetry infrastructure assumptions
- `tests/` for environment bring-up and CI validation needs
- `docs/` for runbooks, architecture docs, and operator guidance

## Forbidden Shortcuts

- Do not commit secrets, certificates, or production credentials.
- Do not let environment-specific patches diverge silently from shared modules or charts.
- Do not use mutable image tags as release truth.
- Do not encode business recovery logic only in infra scripts without matching runbooks.
- Do not let Docker local-compose contracts become the only documented deployment interface.

## Build / Implementation Order

1. Define runtime component inventory and environment assumptions.
2. Package components in `infra/docker` and `infra/helm`.
3. Define shared durable infrastructure and outputs in `infra/terraform`.
4. Bind observability assets to runtime components and critical procedures.
5. Add CI validation for each lane.
6. Update runbooks and environment docs.

## Required Tests / Verification

- Existing structural checks:
  - `find infra -maxdepth 2 -type d | sort`
  - `test -f infra/AGENTS.md`
  - `test -f docs/agents/infra-agent.md`
- Expected command once scaffolded: `make test-infra`
- Expected command once scaffolded: `terraform validate`
- Expected command once scaffolded: `helm lint infra/helm`
- Expected command once scaffolded: `docker build --file infra/docker/<target>/Dockerfile .`

## Required Docs Updates

- Update `docs/runbooks/` when deployment, alerting, or recovery procedures change.
- Update `docs/arc42/` when deployment topology or environment boundaries change.
- Update `docs/api/` if deployment contracts expose external endpoints or webhooks.
- Update `docs/agents/infra-agent.md` and `infra/AGENTS.md` when lane boundaries change.

## Common Failure Modes

- Helm charts grow application-specific logic that should stay in app config.
- Terraform modules encode one environment's accidental constraints as global policy.
- Docker files become the de facto release definition instead of Helm or Terraform inputs.
- Observability assets are created without runbook links or ownership.
- Secrets handling is implied rather than explicit.

## Handoff Contract

- Report lanes changed and affected environments.
- Identify packaging, infrastructure, image, or observability impacts.
- State secrets-handling assumptions and required operator inputs.
- Report verification run and required runbook updates.
- Leave dependency notes for app, adapter, tests, or docs owners when runtime assumptions change.

## Done Criteria

- Infra lanes remain distinct and non-overlapping.
- Secrets remain external to git.
- Release artifacts are immutable and reproducible.
- CI validation expectations are documented for each lane.
- Runbooks and architecture docs reflect deployment or alerting changes.

## Example Prompts For This Agent

- "Define the Helm chart ownership and values contract for the control API and worker services."
- "Add Terraform module boundaries for shared Postgres and Vault while leaving business config out of infra."
- "Document the observability assets needed for workflow retries and contract negotiation failures."
