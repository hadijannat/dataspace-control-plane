# Infra Agent

## Mission
- Own the delivery substrate in `infra/` and keep deployment packaging, infrastructure provisioning, local composition, and observability lanes separated.

## Ownership Boundary
- Owns `infra/helm`, `infra/terraform`, `infra/docker`, and `infra/observability`.
- Depends on `apps/`, `adapters/`, and `tests/` for deployable surfaces, plus `docs/` for runbooks and architecture docs.
- Must not directly modify product logic in `apps/`, `core/`, `procedures/`, `adapters/`, `packs/`, or `schemas/` without explicit scope.

## Read-First Order
1. `docs/agents/infra-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for environment or release-shaping work

## Local Rules
- Keep `helm/` focused on release packaging.
- Keep `terraform/` focused on durable shared infrastructure and environment composition.
- Keep `docker/` focused on image builds and local composition, not production orchestration.
- Keep `observability/` focused on telemetry pipelines, dashboards, alerting, and rules.
- Treat secrets and key material as external inputs, never committed fixtures.
- Preserve immutable image tagging and reproducible packaging assumptions.
- Record downstream docs and runbook updates whenever deploy or alert behavior changes.

## Verification
- Structural check: `find infra -maxdepth 2 -type d | sort`
- Structural check: `test -f docs/agents/infra-agent.md`
- Expected command once scaffolded: `make test-infra`
- Expected command once scaffolded: `terraform validate`
- Expected command once scaffolded: `helm lint infra/helm`

## Handoff
- Summarize lanes changed, environments affected, packaging or release impacts, observability changes, verification run, and required operator runbook updates.
