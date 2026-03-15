# Tests Agent Guidebook

## Purpose
- Own `tests/` as the repo-wide verification spine. These suites validate cross-package behavior, release gates, and architecture boundaries, not just local units.

## Scope
- Define the shared verification topology.
- Maintain release-gate suites across interoperability, tenancy, trust, and chaos scenarios.
- Keep fixtures, environments, and failure artifacts explicit.
- Guard against regressions that cross top-level ownership boundaries.

## Owned Paths
- `tests/unit`
- `tests/integration`
- `tests/e2e`
- `tests/compatibility/dsp-tck`
- `tests/compatibility/dcp-tck`
- `tests/tenancy`
- `tests/crypto-boundaries`
- `tests/chaos`

## Explicitly Non-Owned Paths
- `apps/`
- `core/`
- `procedures/`
- `adapters/`
- `packs/`
- `schemas/`
- `infra/`
- `docs/`

## What This Agent Must Read First
1. `tests/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for new release gates or environment changes
5. Relevant product guidebooks for the surfaces being verified

## Architecture Invariants
- `pytest` is the primary harness unless a compatibility suite requires an auxiliary runner.
- Browser e2e belongs in `tests/e2e`, not inside app packages.
- Compatibility suites validate protocol conformance, not business logic alone.
- Tenancy and crypto-boundary suites are release gates.
- Tests must not require secrets committed in the repo.
- Temporal replay and workflow integration checks belong in repo-wide verification, not only local package tests.

## Subdirectory-By-Subdirectory Responsibilities
### `tests/unit`
- Purpose: fast verification of isolated package behavior, canonical invariants, schema validation, and small integration boundaries
- Allowed dependencies: package-local test helpers, deterministic fixtures, lightweight mocks
- Expected environment: local process only
- Artifacts produced: concise failure reports, coverage, fixture snapshots if needed
- Pass or fail gates: must stay fast and deterministic; failing unit tests block all merges

### `tests/integration`
- Purpose: verify cross-package behavior across apps, procedures, adapters, packs, and schemas
- Allowed dependencies: local services, ephemeral databases, workflow test harnesses, pinned test artifacts
- Expected environment: controlled local or CI stack with service dependencies
- Artifacts produced: logs, traces, workflow histories, integration snapshots
- Pass or fail gates: required for merges affecting inter-package contracts

### `tests/e2e`
- Purpose: validate operator flows from web console through control API and worker-driven workflow surfaces
- Allowed dependencies: browser automation, seeded app stack, generated API clients or fixtures
- Expected environment: running app surfaces plus test identity setup
- Artifacts produced: screenshots, videos if enabled, browser console logs, step traces
- Pass or fail gates: block releases for operator-facing regressions

### `tests/compatibility/dsp-tck`
- Purpose: validate Dataspace Protocol compatibility against pinned expectations or TCK flows
- Allowed dependencies: adapter test harnesses, protocol fixtures, profile-specific datasets
- Expected environment: protocol-capable adapter stack and pinned contexts
- Artifacts produced: conformance reports, failing case logs, protocol transcripts
- Pass or fail gates: release gate for DSP-facing changes

### `tests/compatibility/dcp-tck`
- Purpose: validate DCP compatibility once supported protocol surfaces are scaffolded
- Allowed dependencies: DCP fixtures, adapter harnesses, capability negotiation stubs
- Expected environment: DCP-capable stack or compatibility harness
- Artifacts produced: conformance reports and capability mismatch logs
- Pass or fail gates: release gate for DCP-facing changes

### `tests/tenancy`
- Purpose: verify tenant isolation, delegated admin boundaries, operator-access enforcement, and topology separation
- Allowed dependencies: seeded topology fixtures, operator IAM stubs, workflow and API surfaces
- Expected environment: multi-tenant seeded environment
- Artifacts produced: isolation reports, authorization failure logs, audit event checks
- Pass or fail gates: release gate for any topology or access change

### `tests/crypto-boundaries`
- Purpose: verify key handling, vault integration boundaries, credential flow isolation, and secret non-disclosure
- Allowed dependencies: fake or ephemeral KMS, test certificates, trust fixtures without production material
- Expected environment: isolated trust test environment
- Artifacts produced: trust-boundary reports, redaction checks, key-use traces
- Pass or fail gates: release gate for machine-trust or credential changes

### `tests/chaos`
- Purpose: verify resilience around workflow retries, adapter failures, connector outages, and partial trust degradation
- Allowed dependencies: failure injection harnesses, temporal replay tools, observability capture
- Expected environment: isolated integration environment with fault injection
- Artifacts produced: incident timelines, retry traces, resilience metrics
- Pass or fail gates: required for critical workflows and operator recovery paths

## Allowed Dependencies
- Every product root as a subject under test
- `infra/` for environment definitions
- `docs/` for runbook alignment and failure interpretation

## Forbidden Shortcuts
- Do not hide release gates inside ad hoc package-level tests.
- Do not use production secrets or copied trust material.
- Do not make compatibility suites rely on live internet fetches for contexts or fixtures.
- Do not collapse tenancy or crypto-boundary assertions into generic integration smoke tests.
- Do not accept flaky workflow replay coverage.

## Build / Implementation Order
1. Unit coverage for local invariants and validators
2. Integration coverage for cross-root contracts
3. Replay-safe workflow verification
4. Compatibility suites for protocol surfaces
5. Tenancy and crypto-boundary release gates
6. E2E operator flows
7. Chaos and resilience validation for critical paths

## Required Tests / Verification
- Existing structural checks:
  - `find tests -maxdepth 3 -type d | sort`
  - `test -f tests/AGENTS.md`
  - `test -f docs/agents/tests-agent.md`
- Expected command once scaffolded: `pytest`
- Expected command once scaffolded: `pytest tests/compatibility/dsp-tck`
- Expected command once scaffolded: `pytest tests/compatibility/dcp-tck`
- Expected command once scaffolded: `pytest tests/tenancy`
- Expected command once scaffolded: `pytest tests/crypto-boundaries`

## Required Docs Updates
- Update `docs/runbooks/` when failure interpretation or operator recovery steps change.
- Update `docs/api/` when contract tests expose or require contract documentation changes.
- Update `docs/arc42/` when release gates or verification strategy change architecture assumptions.
- Update `docs/agents/tests-agent.md` and `tests/AGENTS.md` when suite boundaries or gates change.

## Common Failure Modes
- E2E coverage moves into app packages and loses cross-package perspective.
- Compatibility suites drift from pinned protocol fixtures.
- Tenancy checks only test happy paths and miss cross-tenant leakage.
- Crypto-boundary tests log secret material or use real trust assets.
- Chaos testing is skipped for workflow-heavy recovery paths.

## Handoff Contract
- Report suites changed and why.
- Identify required environments, fixtures, and produced artifacts.
- Call out new or tightened release gates.
- Report verification run and unresolved flakiness or coverage gaps.
- Leave dependency notes for owning product directories if failures expose missing behavior.

## Done Criteria
- Suite ownership remains clear by test purpose.
- `pytest` remains the primary harness unless explicitly incompatible.
- Compatibility, tenancy, and crypto-boundary gates are explicit.
- Tests remain secret-free and deterministic where possible.
- Failure artifacts help operators and reviewers diagnose issues.

## Example Prompts For This Agent
- "Add a tenancy release gate under `tests/tenancy` for delegated tenant administration."
- "Create replay and integration checks for the contract negotiation workflow and keep them under top-level `tests/`."
- "Define compatibility fixtures for DSP conformance without relying on live network contexts."
