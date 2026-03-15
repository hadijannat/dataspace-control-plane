# PLANS.md

## When To Use A Plan
- Write a plan for multi-hour tasks.
- Write a plan for cross-directory changes.
- Write a plan for major refactors.
- Write a plan for work that touches architecture boundaries, data contracts, trust boundaries, or release gates.

## Required Plan Shape
1. Objective
2. Affected directories
3. Architecture constraints
4. File-level plan
5. Verification
6. Docs updates
7. Rollback or compatibility concerns

## Planning Rules
- Keep the plan grounded in this monorepo's ownership model.
- Name the owning directory for each change.
- Call out dependencies that require another directory owner.
- Distinguish implemented work from follow-up work.
- Treat the plan as a living document and update it as scope, sequencing, or verification changes.

## Repo-Specific Expectations
- Preserve layer boundaries: `core` defines meaning, `procedures` orchestrate, `adapters` integrate, `packs` overlay rules, `schemas` store machine-readable artifacts, `apps` expose runtime surfaces, `tests` define repo-wide verification, `infra` delivers runtime substrate, `docs` explains and governs the system.
- Include docs work whenever interfaces, architecture, procedures, or operator workflows change.
- Include rollback or compatibility notes for external protocols, packs, schemas, workflows, and infrastructure packaging.
