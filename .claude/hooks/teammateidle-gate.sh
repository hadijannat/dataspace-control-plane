#!/usr/bin/env bash
# TeammateIdle hook: blocks idle if the teammate's handoff file is missing.
# Exit 2 = block idle with message.
# Exit 0 = allow.
# Defensive: exits 0 with warning if teammate-to-directory mapping cannot be determined.
set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HANDOFFS_DIR="${DATASPACE_HANDOFFS_DIR:-.claude/handoffs}"

# Read stdin JSON
PAYLOAD=$(cat)

# Extract teammate_id from payload (experimental hook format — best effort)
TEAMMATE_ID=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.argv[1])
    tid = (data.get('teammate_id') or data.get('teammate') or
           data.get('agent_id') or data.get('agent') or '')
    print(tid)
except Exception:
    print('')
" "$PAYLOAD" 2>/dev/null || echo "")

if [ -z "$TEAMMATE_ID" ]; then
    echo "WARNING: TeammateIdle hook could not determine teammate ID. Handoff check skipped." >&2
    exit 0
fi

# Map teammate_id to directory name
DIR_NAME=$(echo "$TEAMMATE_ID" | sed 's/-lead$//' | tr '[:upper:]' '[:lower:]')

case "$DIR_NAME" in
    core|schemas|adapters|procedures|apps|packs|tests|infra|docs) ;;
    *)
        echo "WARNING: Teammate '$TEAMMATE_ID' maps to unknown directory '$DIR_NAME'. Handoff check skipped." >&2
        exit 0
        ;;
esac

HANDOFF_FILE="$REPO_ROOT/$HANDOFFS_DIR/$DIR_NAME.md"

if [ ! -f "$HANDOFF_FILE" ]; then
    echo "IDLE BLOCKED: teammate must write handoff to $HANDOFFS_DIR/$DIR_NAME.md before going idle."
    echo "Run /request-handoff $DIR_NAME to generate the template."
    echo "Required fields: scope completed, files changed, verification run, downstream impact."
    exit 2
fi

exit 0
