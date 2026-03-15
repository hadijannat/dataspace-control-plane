---
name: close-wave
description: Verify all handoffs are present for changed directories, emit closure checklist, and prepare for next wave.
---
# Close Wave

## Steps

1. **Check all handoffs are present.**
   Run `git diff --name-only HEAD` to find changed top-level directories.
   For each product directory (`core`, `schemas`, `adapters`, `procedures`, `apps`,
   `packs`, `tests`, `infra`, `docs`) that has changes:
   - Check if `.claude/handoffs/<dir>.md` exists.
   - If any are missing: **return an error** — the wave cannot be closed.

   Error message format:
   ```
   WAVE CLOSE BLOCKED: Missing handoff files for directories with changes:
     - .claude/handoffs/<dir>.md (MISSING)
   Run /request-handoff <dir> for each missing directory, then retry /close-wave.
   ```

2. **Verify integration is complete.**
   Check that `/integrate-wave` has been run (PLANS.md has a wave completion entry).
   If not, warn the lead to run `/integrate-wave` first.

3. **Output closure checklist.**
   Emit a checklist the lead must confirm before the wave is considered done:

   ```markdown
   ## Wave Close Checklist

   ### Teammate Shutdown
   - [ ] All teammate agents have been stopped or gone idle
   - [ ] No active teammate sessions remain

   ### Handoff Artifacts
   - [ ] .claude/handoffs/core.md     (if core changed)
   - [ ] .claude/handoffs/schemas.md  (if schemas changed)
   - [ ] .claude/handoffs/adapters.md (if adapters changed)
   - [ ] .claude/handoffs/procedures.md (if procedures changed)
   - [ ] .claude/handoffs/apps.md     (if apps changed)
   - [ ] .claude/handoffs/packs.md    (if packs changed)
   - [ ] .claude/handoffs/tests.md    (if tests changed)
   - [ ] .claude/handoffs/infra.md    (if infra changed)
   - [ ] .claude/handoffs/docs.md     (if docs changed)

   ### Verification
   - [ ] All changed directories have passed their verification gate
   - [ ] Release-gate suites ran (compatibility, tenancy, crypto-boundaries) if applicable

   ### Integration
   - [ ] PLANS.md updated with wave completion entry
   - [ ] Cross-directory dependency notes recorded for next wave

   ### Downstream Notes
   - [ ] All "Downstream Impact" items routed to owning directories
   - [ ] No unresolved blockers that affect next wave kickoff
   ```

4. **Remind the lead to clean up the team.**
   Before starting the next wave:
   - Shut down all current teammate agents
   - Resolve any handoff gaps
   - Use `/start-wave <N+1>` to begin fresh with next wave's teammate set
