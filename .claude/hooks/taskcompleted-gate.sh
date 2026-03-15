#!/usr/bin/env bash
# TaskCompleted hook: gates task completion on three conditions:
#   1. Teammate's handoff file exists.
#   2. Changed files stay within the teammate's owned directory (or approved shared paths).
#   3. Handoff's "## Verification Run" section contains real command output (not template placeholder).
# Exit 2 = block completion with message.
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
    echo "WARNING: TaskCompleted hook could not determine teammate ID. Gate checks skipped." >&2
    exit 0
fi

# Map teammate_id to directory name (convention: <dir>-lead → <dir>)
DIR_NAME=$(echo "$TEAMMATE_ID" | sed 's/-lead$//' | tr '[:upper:]' '[:lower:]')

case "$DIR_NAME" in
    core|schemas|adapters|procedures|apps|packs|tests|infra|docs) ;;
    *)
        echo "WARNING: Teammate '$TEAMMATE_ID' maps to unknown directory '$DIR_NAME'. Gate checks skipped." >&2
        exit 0
        ;;
esac

# --- Gate 1: Handoff file must exist ---
HANDOFF_FILE="$REPO_ROOT/$HANDOFFS_DIR/$DIR_NAME.md"
if [ ! -f "$HANDOFF_FILE" ]; then
    echo "TASK COMPLETION BLOCKED: Handoff file required before task can complete."
    echo "Missing: $HANDOFFS_DIR/$DIR_NAME.md"
    echo "Run '/request-handoff $DIR_NAME' to generate the handoff template, then write to the file."
    exit 2
fi

# --- Gate 2: Changed files must be within the owned directory or approved shared paths ---
# Approved shared paths that any teammate may touch (read-only paths produce no diff entries):
APPROVED_SHARED=(
    ".claude/handoffs/"   # teammate's own handoff file
    ".claude/config-audit.log"
)

# Get files changed since HEAD
CHANGED=$(git diff --name-only HEAD 2>/dev/null || echo "")

if [ -n "$CHANGED" ]; then
    VIOLATIONS=""
    while IFS= read -r file; do
        [ -z "$file" ] && continue
        # Allow if file is within the owned directory
        if [[ "$file" == "$DIR_NAME/"* ]]; then
            continue
        fi
        # Allow if file is in an approved shared path
        ALLOWED=false
        for shared in "${APPROVED_SHARED[@]}"; do
            if [[ "$file" == "$shared"* ]]; then
                ALLOWED=true
                break
            fi
        done
        if [ "$ALLOWED" = false ]; then
            VIOLATIONS="${VIOLATIONS}  ${file}\n"
        fi
    done <<< "$CHANGED"

    if [ -n "$VIOLATIONS" ]; then
        echo "TASK COMPLETION BLOCKED: Files changed outside owned directory '$DIR_NAME/':"
        printf "%b" "$VIOLATIONS"
        echo "Each teammate must only modify its owned root. Cross-boundary changes must be"
        echo "recorded as dependency notes in .claude/handoffs/$DIR_NAME.md, not implemented."
        exit 2
    fi
fi

# --- Gate 3: Handoff must contain a non-placeholder Verification Run section ---
# Check that "## Verification Run" section contains at least one command line or result marker.
# Blocks if the section only has the template comment placeholder.
VERIFICATION_CONTENT=$(python3 -c "
import sys, re
try:
    text = open(sys.argv[1]).read()
    # Extract the Verification Run section (between ## Verification Run and the next ## heading)
    match = re.search(r'## Verification Run(.*?)(?=^##|\Z)', text, re.DOTALL | re.MULTILINE)
    if not match:
        print('missing_section')
    else:
        body = match.group(1).strip()
        # Strip template placeholder comments
        body_no_comments = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL).strip()
        # Look for actual content: command patterns or result markers
        has_content = bool(re.search(
            r'(find |make |pytest |uv |pnpm |helm |terraform |markdownlint |gradlew |\\.\/|✓|✗|PASS|FAIL|passed|failed|error)',
            body_no_comments, re.IGNORECASE
        ))
        print('ok' if has_content else 'empty')
except Exception as e:
    print('error:' + str(e))
" "$HANDOFF_FILE" 2>/dev/null || echo "error")

case "$VERIFICATION_CONTENT" in
    ok)
        ;;
    missing_section)
        echo "TASK COMPLETION BLOCKED: Handoff file is missing the '## Verification Run' section."
        echo "File: $HANDOFFS_DIR/$DIR_NAME.md"
        echo "Add verification commands and their outcomes before completing."
        exit 2
        ;;
    empty)
        echo "TASK COMPLETION BLOCKED: Handoff '## Verification Run' section contains only the template placeholder."
        echo "File: $HANDOFFS_DIR/$DIR_NAME.md"
        echo "Record the actual commands run and their results (✓ / ✗) in the Verification Run section."
        exit 2
        ;;
    *)
        # Parse error or unexpected state — allow with warning (fail open)
        echo "WARNING: Could not parse Verification Run section in $HANDOFFS_DIR/$DIR_NAME.md. Allowing completion." >&2
        ;;
esac

exit 0
