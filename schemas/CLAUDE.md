# schemas — CLAUDE.md

## Purpose
Machine-readable artifact registry: pinned upstream standards, repo-authored validation schemas, derived bundles, examples, and provenance metadata.

## Architecture Invariants
- **JSON Schema 2020-12** for all repo-authored validation schemas, unless a pinned upstream artifact requires another dialect.
- **All upstream artifacts must be pinned with explicit provenance:** source URL, version, content hash, and retrieval date. Never fetch normative artifacts at runtime.
- **Clear labeling:** every artifact is tagged as one of: `source/vendor`, `local-authored`, `derived-bundle`, or `example`.
- **Business meaning stays in `core/`.** `schemas/` stores machine-readable validation rules and pinned artifacts — not semantic definitions.
- **Every schema family needs positive and negative examples** to drive adapter and procedure validation.

## Forbidden Shortcuts
- Do not derive canonical meaning from schema structure — that belongs in `core/`.
- Do not reference upstream normative artifacts by URL at runtime — pin them locally.
- Do not mix source, local, and derived artifacts in the same subdirectory without labeling.

## Allowed Dependencies
- `core/` — canonical models inform schema vocabulary (read only)
- `packs/` — pack overlays may specify required schema extensions (read only)
- Pinned upstream standards (AAS/IDTA, ODRL, W3C VC, DSP, ESPR)

## Verification
```bash
# Structural check
find schemas -maxdepth 2 -type d | sort

# Schema validation (once scaffolded)
make test-schemas
pytest tests/unit -k schemas
pytest tests/compatibility -k schema
```

## Required Docs Updates
When `schemas/` changes:
- Update `docs/api/` if validation contracts change for external consumers
- Update provenance lock files whenever upstream artifacts are updated
- Notify `adapters-lead` and `procedures-lead` of compatibility-impacting schema changes

## Handoff Protocol
Write to `.claude/handoffs/schemas.md` before going idle. Required fields:
- Artifacts added or changed (with provenance details)
- Validation dialect or constraint changes
- Examples added or updated
- Downstream compatibility notes (which adapters/procedures must update)
- Verification run outcome

## Full Guidebook
`docs/agents/schemas-agent.md`
