#!/usr/bin/env bash
# Stop hook: blocks stopping if handoff files are missing for directories with git changes.
# Exit 2 = block stop with message. Exit 0 = allow.
# Per guide: Stop hook must block when required handoff files are missing.
set -uo pipefail

HANDOFFS_DIR="${DATASPACE_HANDOFFS_DIR:-.claude/handoffs}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Get top-level directories changed since HEAD
CHANGED_DIRS=$(git diff --name-only HEAD 2>/dev/null | awk -F/ '{print $1}' | sort -u)

if [ -z "$CHANGED_DIRS" ]; then
    exit 0
fi

MISSING=()
for dir in $CHANGED_DIRS; do
    # Only check product/infra directories (skip .claude, .git, etc.)
    case "$dir" in
        core|schemas|adapters|procedures|apps|packs|tests|infra|docs)
            HANDOFF_FILE="$REPO_ROOT/$HANDOFFS_DIR/$dir.md"
            if [ ! -f "$HANDOFF_FILE" ]; then
                MISSING+=("$dir")
            fi
            ;;
    esac
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "STOP BLOCKED: Session has git changes but missing handoff files."
    echo "Each changed directory must have a handoff before the wave closes."
    for dir in "${MISSING[@]}"; do
        echo "  Missing: $HANDOFFS_DIR/$dir.md"
    done
    echo ""
    echo "For each missing directory: run /request-handoff <dir>, fill the template,"
    echo "then write to .claude/handoffs/<dir>.md before stopping."
    echo "Once all handoffs are present, run /close-wave and then stop."
    exit 2
fi

exit 0
