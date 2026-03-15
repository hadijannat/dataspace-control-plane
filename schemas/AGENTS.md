# Schemas Agent

## Mission
- Own `schemas/` as the machine-readable artifact registry for pinned upstream standards, local schemas, derived bundles, examples, and provenance.

## Ownership Boundary
- Owns `schemas/aas`, `schemas/odrl`, `schemas/vc`, `schemas/dpp`, `schemas/metering`, and `schemas/enterprise-mapping`.
- Depends on `core/` for canonical terms, `packs/` for overlay requirements, `tests/` for validation gates, and `docs/` for schema documentation.
- Must not directly modify `core/`, `adapters/`, `procedures/`, `apps/`, or `infra/` without explicit scope.

## Read-First Order
1. `docs/agents/schemas-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for schema family or validation-dialect changes

## Local Rules
- Keep business semantics in `core/`, not in schema artifacts.
- Use JSON Schema 2020-12 for repo-authored validation schemas unless a pinned upstream artifact requires another dialect.
- Distinguish source, local, derived, and example artifacts clearly.
- Pin upstream JSON-LD contexts and other normative assets with provenance.
- Maintain positive and negative examples for every repo-authored family.
- Do not let vendor-specific transport payloads leak into canonical schema bundles.
- Record lock or provenance updates whenever artifacts move.

## Verification
- Structural check: `find schemas -maxdepth 2 -type d | sort`
- Structural check: `test -f docs/agents/schemas-agent.md`
- Expected command once scaffolded: `make test-schemas`
- Expected command once scaffolded: `pytest tests/unit -k schemas`
- Expected command once scaffolded: `pytest tests/compatibility -k schema`

## Handoff
- Summarize schema families changed, provenance updates, derived artifact impact, validation coverage, examples added, and required downstream docs or adapter work.
