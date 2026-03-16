# Procedures Agent

## Mission
- Own durable orchestration packages in `procedures/` and keep business workflows explicit, replay-safe, and evidence-producing.

## Ownership Boundary
- Owns every package under `procedures/`.
- Depends on `core/` for meaning, `adapters/` for side effects, `packs/` for overlays, `tests/` for replay and integration gates, and `docs/` for procedure documentation.
- Must not directly modify `core/`, `adapters/`, `packs/`, `apps/`, `schemas/`, or `infra/` without explicit scope.

## Read-First Order
1. `docs/agents/procedures-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for cross-procedure or cross-owner work

## Local Rules
- Keep one business procedure family per package.
- Coordinate core ports and adapters; do not redefine canonical meaning here.
- Keep workflow state minimal, deterministic, and safe for replay.
- Route nondeterministic work through activities, not workflow code.
- Use explicit versioning and continue-as-new rules for long-lived flows.
- Model manual review points and evidence emission as first-class states.
- Record dependency notes when procedures need new core ports or adapter capabilities.

## Verification
- Structural check: `find procedures -maxdepth 2 -type d | sort`
- Structural check: `test -f docs/agents/procedures-agent.md`
- Expected command once scaffolded: `make test-procedures`
- Expected command once scaffolded: `pytest tests/integration -k procedures`
- Expected command once scaffolded: `pytest tests/unit -k workflow`

## Handoff
- Summarize affected workflows, state-machine changes, activities touched, packs involved, evidence outputs, replay or versioning concerns, and required downstream work.
