# Apps Agent

## Mission
- Own runtime entrypoints in `apps/` and keep them thin, compositional, and aligned to the semantic and orchestration layers below them.

## Ownership Boundary
- Owns `apps/web-console`, `apps/control-api`, `apps/temporal-workers`, `apps/edc-extension`, and `apps/provisioning-agent`.
- Depends on `core/`, `procedures/`, `adapters/`, `packs/`, `schemas/`, `tests/`, `infra/`, and `docs/`.
- Must not directly modify neighboring roots without explicit task scope.

## Read-First Order
1. `docs/agents/apps-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for large or cross-directory work

## Local Rules
- Keep UI code in `apps/web-console`; do not let it call adapters directly.
- Keep `apps/control-api` as the human-facing and public API surface; route long-running work into procedures and workers.
- Register workflows and activities in `apps/temporal-workers`, but keep canonical meaning in `core/`.
- Keep `apps/edc-extension` thin and runtime-specific.
- Keep `apps/provisioning-agent` declarative; do not reimplement workflow orchestration there.
- Prefer generated clients and shared contracts over handwritten API drift.
- Never store machine-trust private material in browser code.

## Verification
- Structural check: `find apps -maxdepth 2 -type d | sort`
- Structural check: `test -f docs/agents/apps-agent.md`
- Expected command once scaffolded: `make test-apps`
- Expected command once scaffolded: `pytest tests/integration -k apps`
- Expected command once scaffolded: `pytest tests/e2e -k web_console`

## Handoff
- Summarize changed app surfaces, workflow launch points, API or client contract changes, verification run, docs touched, and any required follow-up in `core/`, `procedures/`, `adapters/`, or `infra/`.
