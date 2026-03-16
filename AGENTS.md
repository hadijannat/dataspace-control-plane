# AGENTS.md

## Project Overview
- `dataspace-control-plane` is a monorepo for a multi-ecosystem dataspace control plane. It separates semantic core logic, durable business procedures, external-system adapters, ecosystem packs, schema artifacts, runtime apps, verification, delivery infrastructure, and curated documentation so agents can change one layer without silently redefining another.

## Directory Ownership
- `apps/` owner
- `core/` owner
- `procedures/` owner
- `adapters/` owner
- `packs/` owner
- `schemas/` owner
- `tests/` owner
- `infra/` owner
- `docs/` owner

## Working Model
- Each top-level directory has one specialist owner.
- The closest `AGENTS.md` overrides broader repo guidance for that subtree.
- If a task crosses ownership boundaries, stop at the owned boundary, make the local change only, and leave a dependency note for the neighboring owner or lead orchestrator.

## Rules
- Do not edit files outside the owned top-level directory unless the prompt explicitly allows it.
- If cross-directory changes are needed, update owned code only and record the missing upstream or downstream work.
- Read the local guidebook in `docs/agents/` before changing files in a top-level directory.
- Use `PLANS.md` for large, cross-directory, or architecture-shaping work.
- Run the relevant verification steps for the owned directory before finishing.
- Update documentation when architecture, interfaces, operational workflows, or ownership assumptions change.

## Review Guidelines
- Do not log secrets, credential material, regulated data, or personally identifiable information.
- Verify tenancy boundaries, operator boundaries, and machine-trust boundaries on every change.
- Preserve cross-layer rules: core meaning stays in `core/`, orchestration stays in `procedures/`, integration stays in `adapters/`, overlays stay in `packs/`.
- Prefer additive, explicit changes over hidden rewrites across ownership lines.

## Pointers
- Guidebook index: `docs/agents/index.md`
- Ownership map: `docs/agents/ownership-map.md`
- Planning rules: `PLANS.md`
- Repo-local skills: `.agents/skills/`
