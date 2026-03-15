---
name: start-wave
description: Launch a build wave — run Plan Mode first, then spawn teammates with enforced coordinator mode.
---
# Start Wave

## Steps

### Step 1 — Identify the wave number.
Ask the user which wave to start if not provided:
- Wave 0 — foundation-planning: `core-lead`, `schemas-lead`, `infra-lead`, `docs-lead`
- Wave 1 — platform-foundation: `core-lead`, `schemas-lead`, `adapters-lead`, `infra-lead`
- Wave 2 — execution-layer: `procedures-lead`, `apps-lead`, `tests-lead`, `adapters-lead`
- Wave 3 — overlays-hardening: `packs-lead`, `tests-lead`, `docs-lead`

### Step 2 — Run Plan Mode first (REQUIRED before spawning any teammate).
Before creating the team, the lead must:
1. Read the relevant directory `CLAUDE.md` files for each active teammate in this wave.
2. Read `.claude/team-ownership.yaml` to confirm dependencies and forbidden zones.
3. Propose in writing:
   - Active teammates and their owned roots
   - 5–6 concrete tasks per teammate (listed explicitly)
   - Task dependencies between teammates (what must complete before what starts)
   - Approval criteria: what "done" means per teammate
   - Shared-file read-only constraints
4. Wait for explicit user approval of the plan before proceeding to Step 3.

This is the "explore → plan" phase. Do not spawn teammates until the plan is approved.

### Step 3 — Read the wave definition.
Load `.claude/team-ownership.yaml` and extract the matching wave entry (teammates, purpose).

### Step 4 — List active teammates and their owned roots.
For each teammate in the wave, output:
- Teammate name (e.g., `core-lead`)
- Owned root (e.g., `core/`)
- Handoff file (e.g., `.claude/handoffs/core.md`)
- Guidebook: `docs/agents/<dir>-agent.md`

### Step 5 — Emit the team-creation prompt.
Use this natural-language prompt template, filled in for the specific wave:

```
Create an agent team for the dataspace-control-plane repository.

This is Wave <N>: <wave-name>.
Spawn <count> teammates, each using claude-sonnet-4-6:
- <dir1>-lead, owner of <dir1>/
- <dir2>-lead, owner of <dir2>/
[... one entry per active teammate]

Constraints:
- Each teammate owns exactly one top-level directory.
- No teammate may edit another's owned directory. Record dependency notes instead.
- Shared governance files (CLAUDE.md, PLANS.md, AGENTS.md, Makefile, .claude/settings.json,
  CODEOWNERS) are read-only for all teammates.
- Create 5–6 tasks per teammate using the shared task list with dependency ordering.
- Do not let the lead implement code while teammates are active.
  Wait for teammates to complete their tasks before proceeding.
- Each teammate must write .claude/handoffs/<dir>.md before going idle or completing.
- Only accept plans that include explicit verification steps.
- Teammates should message each other directly when blocked by a dependency.
- Summarize blockers to the lead as soon as they appear.

Wave purpose: <purpose from team-ownership.yaml>

Teammate tasks:
  <dir1>-lead (<dir1>/):
    1. <task 1>
    2. <task 2>
    3. <task 3>
    4. <task 4>
    5. <task 5>
  [repeat per teammate]
```

### Step 6 — Enforce lead coordinator mode.
After the team is created, remind the lead:
- **Wait for teammates to complete their tasks before proceeding.**
- Monitor via `Ctrl+T` (task list) and `Shift+Down` (cycle through teammates in in-process mode).
- Route cross-boundary dependency notes between owners as they appear.
- Do NOT implement code or edit product directories while teammates are running.
- Use `/review-wave` to check status at any time.
- Use `/integrate-wave` after all teammates complete and have written handoffs.

## Lead Sequence

```
explore  →  plan (Plan Mode)  →  approve  →  delegate (start-wave)
         →  monitor           →  integrate →  close
```

Never collapse "plan" and "delegate" — the lead stays in Plan Mode until the user approves
the task breakdown. Never collapse "delegate" and "implement" — the lead stays in coordinator
mode until all teammates have written their handoffs and gone idle.
