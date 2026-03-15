---
name: review-wave
description: Read all handoff files, summarize per-teammate status, flag missing handoffs and cross-directory dependencies.
---
# Review Wave

## Steps

1. **Read all handoff files.**
   List and read every file in `.claude/handoffs/` (excluding `README.md`).

2. **Identify directories with recent git changes.**
   Run `git diff --name-only HEAD` and group changed files by top-level directory.
   Cross-reference with handoff files: any changed directory without a handoff is a gap.

3. **Summarize per teammate.**
   For each teammate with a handoff file, output a structured summary:
   - **Scope**: what was done (from "Scope Completed" section)
   - **Files changed**: count and key paths
   - **Tests**: verification outcome (pass / fail / not run)
   - **Blockers**: anything flagged in "Blockers and Open Questions"
   - **Design/contract changes**: anything in "Design / Contract Changes" that downstream owners must read

4. **Flag missing handoffs.**
   List every directory that has git changes but no handoff file.
   Mark these as BLOCKING for wave close (they must be resolved before `/close-wave`).

5. **Surface cross-directory dependency notes.**
   Scan all handoff "Downstream Impact" sections. Produce a dependency table:

   | From | To | Required Follow-up |
   |------|----|--------------------|
   | core | adapters | implement new port X |

6. **Recommend next steps.**
   Based on the review:
   - Which teammates can be considered done?
   - Which still need to complete work or write handoffs?
   - What should the lead communicate to the team before integration?
   - Is the wave ready for `/integrate-wave` or do blockers remain?
