# tests — CLAUDE.md

## Purpose
Repo-wide verification spine: unit, integration, e2e, compatibility (DSP/DCP TCKs), tenancy, crypto-boundary, and chaos suites that validate cross-package behavior and release gates.

## Architecture Invariants
- **`pytest` is the primary harness.** Compatibility suites may use auxiliary runners only where protocol test kits require it.
- **Release gates are non-negotiable.** `tests/compatibility/dsp-tck`, `tests/compatibility/dcp-tck`, `tests/tenancy`, and `tests/crypto-boundaries` must pass before any wave closes.
- **No production secrets in test fixtures.** Use deterministic replay-safe fixtures, mocked credentials, and locally pinned protocol artifacts only.
- **No live internet fetches for protocol fixtures.** Pin all external TCK artifacts locally; integration tests use local test environments.

## Forbidden Shortcuts
- Do not edit product directories (`core/`, `apps/`, etc.) to make tests pass — route failures as dependency notes to the owning specialist.
- Do not skip or mark-xfail compatibility and tenancy gate tests without explicit lead authorization.
- Do not embed real private keys, production API tokens, or operator credentials in test fixtures.

## Allowed Dependencies
- All product roots (read only for fixture discovery)
- `infra/` — environment definitions for integration test infrastructure

## Verification
```bash
# Full test suite
pytest

# Release gate suites
pytest tests/compatibility/dsp-tck
pytest tests/compatibility/dcp-tck
pytest tests/tenancy
pytest tests/crypto-boundaries

# Chaos
pytest tests/chaos
```

## Required Docs Updates
When `tests/` changes:
- Update `docs/runbooks/` if new test environments or fixture setup is required for operators
- Notify the lead if a new release gate is introduced (it blocks wave close)

## Handoff Protocol
Write to `.claude/handoffs/tests.md` before going idle. Required fields:
- Suites changed or added
- New release gates introduced
- Environments required for integration/e2e tests
- Test artifacts produced (coverage, compatibility reports)
- Failures or gaps left for owning directories (with dependency notes)
- Verification run outcome

## Full Guidebook
`docs/agents/tests-agent.md`
