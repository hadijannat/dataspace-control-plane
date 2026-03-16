---
name: implementation-strategy
description: Summarize architecture boundaries, impacted directories, likely verification, and likely docs updates before major edits in this repo.
---

# Implementation Strategy

## When to use
- Use before major edits, cross-directory work, or any task that may cross an ownership boundary.

## Steps
1. Name the primary owned directory and any neighboring directories the task touches indirectly.
2. State the architecture boundary that must remain intact.
3. List likely verification steps for the owned directory.
4. List likely docs updates in `docs/`, `docs/agents/`, or local `AGENTS.md`.
5. Call out dependency notes instead of proposing edits in non-owned roots unless the prompt explicitly authorizes them.

## Output
- A short pre-edit note with:
  - owned directory
  - impacted directories
  - boundary constraints
  - likely tests
  - likely docs updates
