---
name: docs-sync
description: Identify which docs files must change after code changes in this repo and what sections should be updated.
---

# Docs Sync

## When to use
- Use when code, contracts, workflows, deployment behavior, or ownership rules changed and docs follow-up is required.

## Steps
1. Identify the owning directory and the changed surface.
2. Map the change to the right docs families:
  - `docs/api`
  - `docs/runbooks`
  - `docs/arc42`
  - `docs/adr`
  - `docs/threat-model`
  - `docs/compliance-mappings`
  - `docs/agents`
3. For each affected file or doc family, state the exact section to update.
4. Call out any local `AGENTS.md` or guidebook updates if ownership or verification rules changed.

## Output
- A concise list of docs paths or doc families and the sections that need edits.
