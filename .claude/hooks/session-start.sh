#!/usr/bin/env bash
# Session-start hook: injects repo context as additionalContext AND exports env vars
# via CLAUDE_ENV_FILE so every teammate in the session has access to wave state.
# Avoid set -e so partial failures don't block the session.
set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HANDOFFS_DIR="${DATASPACE_HANDOFFS_DIR:-.claude/handoffs}"

# Export wave state into session env via CLAUDE_ENV_FILE (if Claude Code provides it).
# Teammates inherit the lead's env at spawn time, so these vars propagate automatically.
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -f "$CLAUDE_ENV_FILE" ]; then
    echo "DATASPACE_HANDOFFS_DIR=${HANDOFFS_DIR}" >> "$CLAUDE_ENV_FILE"
    echo "DATASPACE_OWNERSHIP_MAP=${REPO_ROOT}/.claude/team-ownership.yaml" >> "$CLAUDE_ENV_FILE"
    echo "DATASPACE_REPO_ROOT=${REPO_ROOT}" >> "$CLAUDE_ENV_FILE"
fi

CONTEXT=$(cat <<'CONTEXT_EOF'
=== dataspace-control-plane — Agent Teams Context ===

WAVE MODEL (4 waves, 3–5 specialist teammates each):
  Wave 0 — foundation-planning:  core-lead, schemas-lead, infra-lead, docs-lead
  Wave 1 — platform-foundation:  core-lead, schemas-lead, adapters-lead, infra-lead
  Wave 2 — execution-layer:      procedures-lead, apps-lead, tests-lead, adapters-lead
  Wave 3 — overlays-hardening:   packs-lead, tests-lead, docs-lead

HANDOFFS DIRECTORY: .claude/handoffs/
  Each teammate writes <dir>.md before going idle or completing a task.
  Template and protocol: .claude/handoffs/README.md

AVAILABLE SKILLS:
  Repo skills (always available via Agent tool):
    handoff-summary         — summarize all current handoff files
    implementation-strategy — plan implementation within owned root
    docs-sync               — check docs/ is current after changes
    directory-verification  — run structural + test verification for a directory

  Wave skills (invoke with /skill-name):
    /start-wave             — kick off a wave (identify wave → list teammates → emit tasks)
    /review-wave            — read handoffs, summarize per-teammate, flag missing
    /request-handoff        — generate pre-filled handoff template for a directory
    /integrate-wave         — synthesize wave into PLANS.md, identify next wave work
    /close-wave             — verify all handoffs present, emit closure checklist

LEAD COORDINATOR RULES:
  1. Sequence: explore → plan → delegate → monitor → integrate → close.
     DO NOT code while teammates are active. Wait for teammates to complete.
  2. Always start a wave in Plan Mode first: explore the repo, read directory CLAUDE.md
     files, propose teammate list, task breakdown, dependencies, and approval criteria
     BEFORE spawning any teammate.
  3. One lead per session. One team per session. Start each wave in a fresh session.
  4. Use /start-wave to launch a wave (includes Plan Mode step + kickoff prompt).
  5. Use Ctrl+T to inspect task list; use Shift+Down to cycle through teammates.
  6. Use /review-wave and /integrate-wave after all teammates complete.
  7. Use /close-wave before shutting down the team. Cleanup must be done by the lead.

CROSS-BOUNDARY RULE:
  Never edit outside your owned root. If a cross-boundary change is needed:
  - Make only the local change.
  - Record a dependency note in your handoff file (.claude/handoffs/<dir>.md).
  - The lead will route the note to the downstream owner.

PROTECTED FILES (cannot be edited by any specialist without lead authorization):
  .claude/settings.json
  CLAUDE.md              (root only — core/CLAUDE.md etc. are NOT protected)
  AGENTS.md              (root only)
  PLANS.md
  CODEOWNERS
  Makefile
  Taskfile.yml / Taskfile.yaml
  .github/pull_request_template.md

SUBAGENT DEFINITIONS: .claude/agents/
  Each file mirrors a directory role. Use Agent tool with the subagent file for
  single-session subagent work (core-lead, schemas-lead, adapters-lead, etc.).

OWNERSHIP MAP: .claude/team-ownership.yaml
  Machine-readable: roots, upstream/downstream deps, forbidden zones, handoff paths.

FULL GUIDEBOOKS: docs/agents/<dir>-agent.md
  Deep architecture rules per directory. Read before editing any owned root.
CONTEXT_EOF
)

echo "$CONTEXT" | python3 -c "
import json, sys
ctx = sys.stdin.read()
print(json.dumps({'additionalContext': ctx}))
"
