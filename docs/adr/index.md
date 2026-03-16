---
title: "Architecture Decision Records"
summary: "Index of all MADR architecture decision records, their status, and links to the full decision documents."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

Architecture Decision Records (ADRs) document the significant design decisions made during platform development. The platform uses [MADR (Markdown Architectural Decision Records)](https://adr.github.io/madr/) format, which provides a lightweight, version-control-friendly structure that integrates naturally with the docs-as-code workflow.

## ADR Status Meanings

| Status | Meaning |
|--------|---------|
| **Proposed** | Decision is under discussion. Not yet authoritative — do not implement based on a proposed ADR alone. |
| **Accepted** | Decision has been reviewed and adopted. Implementations must conform to it. |
| **Deprecated** | Decision was accepted but is no longer recommended. Implementations may still exist but should migrate. |
| **Superseded** | Decision has been replaced by a newer ADR. The superseded ADR links to its replacement. |

## Template

All new ADRs must start from [_template.md](_template.md). The template enforces the MADR structure: front matter, context, decision drivers, options, outcome, consequences, and an optional confirmation section.

## ADR Index

| ADR | Title | Status | Date | Decision-makers | Affected layers |
|-----|-------|--------|------|----------------|----------------|
| [0001](0001-use-mkdocs-material.md) | Use MkDocs + Material for docs-as-code publishing | Accepted | 2026-03-14 | docs-lead | `docs/` |
| [0002](0002-adopt-temporal-as-workflow-engine.md) | Adopt Temporal as the workflow engine | Accepted | 2026-03-14 | docs-lead, all leads | `procedures/`, `apps/`, `tests/` |
| [0003](0003-json-schema-2020-12-as-house-dialect.md) | JSON Schema 2020-12 as the house validation dialect | Accepted | 2026-03-14 | schemas-lead, all leads | `schemas/`, `adapters/`, `packs/` |
| [0004](0004-vault-transit-for-signing-keys.md) | Vault Transit for all signing operations | Accepted | 2026-03-14 | infra-lead, all leads | `procedures/`, `adapters/`, `tests/` |
| [0005](0005-packs-as-pure-overlay.md) | Packs as pure overlays over core semantics | Accepted | 2026-03-14 | packs-lead, core-lead | `packs/`, `core/` |

## How to Add an ADR

1. Determine the next sequence number (increment from the highest existing number).
2. Copy `docs/adr/_template.md` to `docs/adr/NNNN-short-slug.md`.
3. Fill in all front matter fields.
4. Complete all body sections. Be specific about decision drivers — vague drivers make it impossible to evaluate whether the chosen option actually satisfies them.
5. Add the ADR to the index table in this file.
6. Link the ADR from `docs/arc42/09-architecture-decisions.md`.
7. Link the ADR from the relevant arc42 sections (constraints, solution strategy, crosscutting concepts as appropriate).
8. Set `status: proposed` initially. After team review during the relevant wave review session, update to `accepted`.

## Relationship to arc42

Every ADR that is accepted should be referenced from at least one arc42 section:

- If it addresses a constraint → [Section 2](../arc42/02-constraints.md)
- If it is a fundamental architectural bet → [Section 4](../arc42/04-solution-strategy.md)
- If it governs a crosscutting concept → [Section 8](../arc42/08-crosscutting-concepts.md)
- Always listed in → [Section 9](../arc42/09-architecture-decisions.md)
