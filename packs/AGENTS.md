# Packs Agent

## Mission
- Own executable overlays in `packs/` for ecosystem, regulatory, and custom enterprise rules without taking over transport or canonical semantics.

## Ownership Boundary
- Owns `packs/catenax`, `packs/manufacturing-x`, `packs/gaia-x`, `packs/espr-dpp`, `packs/battery-passport`, and `packs/custom`.
- Depends on `core/`, `procedures/`, `schemas/`, `tests/`, and `docs/`.
- Must not directly modify `adapters/`, `apps/`, `infra/`, or `core/` semantics without explicit scope.

## Read-First Order
1. `docs/agents/packs-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for cross-pack or regulation-driven work

## Local Rules
- Keep packs versioned and explicit about effective dates.
- Treat packs as overlays on core meaning and procedures, not replacements for them.
- Pin normative assets locally; do not fetch them at runtime.
- Encode provenance for pack inputs, generated outputs, and evidence requirements.
- Resolve pack conflicts explicitly and document precedence.
- Put ecosystem-specific identifiers and profiles here when they are not canonical.
- Record dependencies when pack changes require schema, adapter, or procedure updates.

## Verification
- Structural check: `find packs -maxdepth 2 -type d | sort`
- Structural check: `test -f docs/agents/packs-agent.md`
- Expected command once scaffolded: `make test-packs`
- Expected command once scaffolded: `pytest tests/integration -k packs`
- Expected command once scaffolded: `pytest tests/unit -k compliance`

## Handoff
- Summarize packs changed, effective-date or profile shifts, normative assets pinned, conflicts resolved, verification run, and required downstream procedure or schema updates.
