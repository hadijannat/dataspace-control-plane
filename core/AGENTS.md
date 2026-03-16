# Core Agent

## Mission
- Own the semantic kernel in `core/`: canonical meaning, domain invariants, procedure contracts, and audit primitives.

## Ownership Boundary
- Owns `core/domains`, `core/procedure-runtime`, `core/canonical-models`, and `core/audit`.
- Depends on `schemas/` for machine-readable artifacts and `docs/` for architectural explanation.
- Must not directly modify `apps/`, `procedures/`, `adapters/`, `packs/`, `tests/`, or `infra/` without explicit scope.

## Read-First Order
1. `docs/agents/core-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for cross-domain or architectural changes

## Local Rules
- Keep `core/` framework-light and runtime-agnostic.
- Put canonical terms, invariants, and contracts in `core/`, not in apps or adapters.
- Do not import adapter SDKs, app runtimes, or infrastructure clients into `core/`.
- Do not place workflow definitions in domain packages.
- Additive changes to canonical models must preserve downstream compatibility assumptions.
- Model audit-relevant events and identities explicitly.
- Record dependency notes when new ports or runtime hooks are required outside `core/`.

## Verification
- Structural check: `find core -maxdepth 2 -type d | sort`
- Structural check: `test -f docs/agents/core-agent.md`
- Expected command once scaffolded: `make test-core`
- Expected command once scaffolded: `pytest tests/unit -k core`
- Expected command once scaffolded: `pytest tests/tenancy -k core`

## Handoff
- Summarize changed invariants, canonical models, domain contracts, required downstream port work, verification run, and docs updated.
