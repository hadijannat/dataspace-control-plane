# packs — CLAUDE.md

## Purpose
Ecosystem and regulatory overlays: versioned profile behavior, evidence requirements, and policy constraints for Catena-X, Gaia-X, manufacturing-x, ESPR-DPP, and battery-passport — layered on top of `core/` without redefining canonical meaning.

## Architecture Invariants
- **Overlays only, not the semantic source of truth.** `core/` defines meaning; packs add versioned profile behavior, evidence rules, delegated-act requirements, and policy constraints.
- **Normative assets must be pinned locally.** Regulation texts, standards documents, and schema profiles must be stored with provenance — no runtime network fetch.
- **Transport code stays in `adapters/`.** Packs must not implement HTTP clients, protocol handlers, or persistence.
- **Cross-pack conflicts must be declared explicitly.** When two packs define overlapping rules (e.g., Catena-X and ESPR-DPP both constrain a policy field), the conflict and resolution must be documented in the pack manifests.

## Forbidden Shortcuts
- Do not define canonical domain types — consume from `core/`.
- Do not implement protocol or transport logic — that belongs in `adapters/`.
- Do not silently resolve cross-pack conflicts — document them.

## Allowed Dependencies
- `core/` — canonical models and domain invariants (read only)
- `schemas/` — pinned normative schema artifacts (read only)
- `docs/compliance-mappings/` — regulation mapping context (read only)

## Verification
```bash
# Structural check
find packs -maxdepth 2 -type d | sort

# Pack and compatibility tests (once scaffolded)
make test-packs
pytest tests/integration -k packs
pytest tests/compatibility -k packs
```

## Required Docs Updates
When `packs/` changes:
- Update `docs/compliance-mappings/` for regulation or normative reference changes
- Update `docs/arc42/` if new pack family is added
- Notify `procedures-lead` if workflow branching changes due to pack rules
- Notify `schemas-lead` if new schema families are needed

## Handoff Protocol
Write to `.claude/handoffs/packs.md` before going idle. Required fields:
- Packs changed (which ecosystem or regulation overlay, what changed)
- Effective-date or policy version changes
- Normative assets added or pinned (with provenance)
- Cross-pack conflicts declared or resolved
- Required schema or procedure follow-up (dependency notes)
- Verification run outcome

## Full Guidebook
`docs/agents/packs-agent.md`
