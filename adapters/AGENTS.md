# Adapters Agent

## Mission
- Own integration code in `adapters/` and keep external transports, SDKs, and wire models isolated from canonical meaning.

## Ownership Boundary
- Owns `adapters/dataspace`, `adapters/enterprise`, and `adapters/infrastructure`.
- Depends on `core/` for ports and canonical models, `schemas/` for pinned artifacts, `tests/` for compatibility and integration gates, and `docs/` for adapter documentation.
- Must not directly modify `core/`, `procedures/`, `apps/`, `packs/`, or `infra/` without explicit scope.

## Read-First Order
1. `docs/agents/adapters-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for cross-adapter or protocol-shaping changes

## Local Rules
- Implement core ports; do not move external APIs into canonical layers.
- Keep protocol wire models, transport clients, and vendor quirks local to adapter packages.
- Normalize external payloads into canonical models before crossing the boundary.
- Map external failures into explicit, typed domain-facing errors.
- Treat credentials, keys, and tokens as secret material; never log them.
- Keep health, readiness, and retry policy explicit for every adapter family.
- Mark composition adapters separately from leaf adapters in docs and code layout.

## Verification
- Structural check: `find adapters -maxdepth 3 -type d | sort`
- Structural check: `test -f docs/agents/adapters-agent.md`
- Expected command once scaffolded: `make test-adapters`
- Expected command once scaffolded: `pytest tests/integration -k adapters`
- Expected command once scaffolded: `pytest tests/compatibility -k "dsp or dcp"`

## Handoff
- Summarize ports implemented, canonical mappings changed, secret-handling impact, compatibility surfaces affected, verification run, and required upstream or downstream follow-up.
