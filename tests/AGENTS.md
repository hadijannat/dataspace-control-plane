# Tests Agent

## Mission
- Own the repo-wide verification spine in `tests/` and keep release gates explicit across unit, integration, e2e, compatibility, tenancy, crypto, and chaos coverage.

## Ownership Boundary
- Owns all paths under `tests/`.
- Depends on every product root for subjects under test and on `docs/` for operator-facing verification notes.
- Must not directly modify product roots or `infra/` without explicit scope.

## Read-First Order
1. `docs/agents/tests-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for new suites or release-gate changes

## Local Rules
- Treat top-level `tests/` as cross-package verification, not local package leftovers.
- Use `pytest` as the primary harness unless an explicit compatibility tool requires another runner.
- Keep browser e2e coverage under `tests/e2e`.
- Make tenancy and crypto-boundary checks explicit release gates.
- Keep tests free of secrets, production keys, and private trust material.
- Prefer deterministic fixtures and replay-safe Temporal verification.
- Emit artifacts that help operators and leads understand failures.

## Verification
- Structural check: `find tests -maxdepth 3 -type d | sort`
- Structural check: `test -f docs/agents/tests-agent.md`
- Expected command once scaffolded: `pytest`
- Expected command once scaffolded: `pytest tests/compatibility/dsp-tck`
- Expected command once scaffolded: `pytest tests/compatibility/dcp-tck`

## Handoff
- Summarize suites changed, gates introduced or tightened, environments needed, artifacts produced, verification run, and gaps left for owning product directories.
