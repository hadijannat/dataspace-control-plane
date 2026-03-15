---
name: integrate-wave
description: Synthesize completed wave into PLANS.md, surface cross-directory dependencies, and recommend next-wave kickoff.
---
# Integrate Wave

## Steps

1. **Read all handoff files.**
   Read every `.claude/handoffs/<dir>.md` file. Note which directories have handoffs
   and which do not (flag missing ones as not integrated yet).

2. **Synthesize wave summary.**
   Produce a structured integration report:

   **Per-directory achievements:**
   - What was built or established (from "Scope Completed")
   - Verification outcome (from "Verification Run")
   - Key design/contract changes that affect downstream owners

   **Resolved cross-directory dependencies:**
   - Dependency notes that were raised and addressed within this wave

   **Open cross-directory dependencies:**
   - Dependency notes from "Downstream Impact" sections that require next-wave work
   - Format: From → To → Required action

   **Release gate status:**
   - Which test suites passed (from tests-lead handoff if present)
   - Which compatibility/tenancy/crypto-boundary checks ran

3. **Update or create wave entry in PLANS.md.**
   Read `PLANS.md` and add or update a wave completion section:
   ```markdown
   ## Wave <N> — <name> — Completed <date>
   ### Achievements
   ...
   ### Open Dependencies for Wave <N+1>
   ...
   ### Verification Status
   ...
   ```

4. **Identify work for next wave.**
   Based on open downstream dependencies and incomplete areas:
   - Which directories need follow-up?
   - What should be in the next wave's teammate task lists?

5. **Output recommended next-wave kickoff prompt.**
   Emit a `/start-wave <N+1>` invocation prompt with pre-filled context:
   - Tasks to carry forward from open dependencies
   - New work to add based on wave <N> achievements
   - Any architecture constraints raised in handoffs
