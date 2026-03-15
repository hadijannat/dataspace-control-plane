# core — CLAUDE.md

## Purpose
Semantic kernel: defines canonical meaning, domain invariants, procedure contracts, and audit primitives that all other layers consume.

## Architecture Invariants
- **Framework-light.** Pure domain code, interfaces, explicit contracts, small shared primitives only. No adapter types, ORM imports, Temporal SDK, or transport clients.
- **Canonical meaning lives here exactly once.** Packs may overlay policy or profile requirements; they must not fork core semantics.
- **Procedure contracts belong here.** Input/output/evidence shape, retry semantics, and state transition contracts are defined in `core/procedure-runtime/` — not in workflow engine code.
- **No import of app runtimes, deployment packaging, or SDK-specific infrastructure.**
- **Audit is semantic.** `core/audit/` owns audit event shapes and trust-boundary markers — not logging sink implementation.

## Forbidden Shortcuts
- Do not add Temporal workflow or activity decorators to `core/` code.
- Do not import from `adapters/`, `procedures/`, `apps/`, `packs/`, or `infra/`.
- Do not store canonical meaning in more than one place — resolve conflicts by consolidating into `core/`, not by forking.

## Allowed Dependencies
- `schemas/` — for pinned normative identifiers and type definitions
- `docs/` — for architecture context and compliance mappings (read only)

## Verification
```bash
# Structural check
find core -maxdepth 2 -type d | sort

# Unit and trust tests (once scaffolded)
make test-core
pytest tests/unit -k core
pytest tests/tenancy -k core
pytest tests/crypto-boundaries -k trust
```

## Required Docs Updates
When `core/` changes:
- Update `docs/arc42/` if canonical model or domain boundary changes
- Update `docs/agents/core-agent.md` if ownership rules or invariants change
- Update `docs/api/` if procedure contracts change externally-visible behavior
- Record ADR in `docs/adr/` for significant design decisions

## Handoff Protocol
Write to `.claude/handoffs/core.md` before going idle. Required fields:
- Invariant changes (anything that forces downstream owners to adapt)
- Canonical model changes (new types, renamed fields, removed fields)
- New ports defined (what adapters must implement)
- Audit implications (new trust-boundary events)
- Verification run outcome
- Downstream impact per directory

## Full Guidebook
`docs/agents/core-agent.md`
