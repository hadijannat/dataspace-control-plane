# docs — CLAUDE.md

## Purpose
Governance and explanation layer: architecture narratives, ADRs, API contracts, runbooks, threat models, compliance mappings, and agent guidebooks — curated for operators, reviewers, security, compliance, and future agents.

## Architecture Invariants
- **Curated explanation, not a code mirror.** Write for understanding and governance, not to repeat what the code already says. Every document should explain the "why" or "how" that cannot be derived from reading the source.
- **Docs-as-code discipline.** Documents are versioned, reviewable, and cross-linked. File paths are stable references for ADRs and runbooks.
- **Generated vs hand-written are clearly separated.** Mark generated reference docs (e.g., API specs generated from OpenAPI) distinctly from hand-written architecture narratives.
- **Every architecture, interface, or workflow change triggers a doc review.** The `docs-lead` reads all teammate handoffs and updates `docs/` accordingly.

## Forbidden Shortcuts
- Do not put docs site configuration or build tooling outside `docs/` (or `infra/` for hosting).
- Do not replicate code comments verbatim as documentation — add context and rationale.
- Do not skip ADR creation for significant design decisions. A decision not recorded is a decision lost.

## Allowed Dependencies
- All product roots (read only — documentation describes but does not modify)

## Verification
```bash
# Structural check
find docs -maxdepth 2 -type d | sort

# Docs linting (once scaffolded)
make test-docs
markdownlint docs
pytest tests/unit -k docs_links
```

## Required Docs Updates
Triggered by changes to any of:
- `core/` canonical models or procedure contracts → update `docs/arc42/`, `docs/api/`
- `procedures/` workflow families → update `docs/runbooks/`, `docs/arc42/`
- `adapters/` protocol behavior → update `docs/api/`, `docs/arc42/`
- `apps/` API surfaces → update `docs/api/`
- `packs/` regulation overlays → update `docs/compliance-mappings/`
- `infra/` environment or deployment changes → update `docs/runbooks/`
- Any boundary, ownership, or agent rule change → update `docs/agents/`

## Handoff Protocol
Write to `.claude/handoffs/docs.md` before going idle. Required fields:
- Documents changed (ADRs recorded, runbooks updated, guidebooks revised)
- Sources of truth used (which product-root handoffs informed the doc updates)
- Broken links fixed
- Review triggers (which other directories should be notified of doc changes)
- Remaining documentation debt (gaps left for future waves)
- Verification run outcome

## Full Guidebook
`docs/agents/docs-agent.md`
