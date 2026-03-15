---
name: directory-verification
description: Emit the verification checklist and command sequence for a specific top-level directory owner in this repo.
---

# Directory Verification

## When to use
- Use when finishing work in one owned top-level directory.

## Steps
1. Identify the owner root: `apps`, `core`, `procedures`, `adapters`, `packs`, `schemas`, `tests`, `infra`, or `docs`.
2. Read the local `AGENTS.md` and matching `docs/agents/*-agent.md`.
3. Output:
  - structural checks that already exist now
  - expected commands once scaffolded
  - docs checks required for that owner
4. Flag any verification gap caused by missing scaffolding instead of inventing a passing command.

## Output
- A flat checklist with commands and a short note on what is blocked by missing repo scaffolding.
