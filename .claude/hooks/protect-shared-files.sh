#!/usr/bin/env bash
# PreToolUse hook: blocks Write/Edit to protected shared governance files.
# Exit 2 = block with message shown to Claude.
# Exit 0 = allow.
set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Read stdin JSON and extract file_path
FILE_PATH=$(python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    path = data.get('tool_input', {}).get('file_path', '')
    print(path)
except Exception:
    print('')
")

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Normalize to repo-relative path
if [[ "$FILE_PATH" == /* ]]; then
    REL_PATH="${FILE_PATH#$REPO_ROOT/}"
else
    REL_PATH="$FILE_PATH"
fi

# Protected files: exact repo-relative paths
PROTECTED_EXACT=(
    ".claude/settings.json"
    "CLAUDE.md"
    "AGENTS.md"
    "PLANS.md"
    "CODEOWNERS"
    "Makefile"
    "Taskfile.yml"
    "Taskfile.yaml"
    ".github/pull_request_template.md"
)

for protected in "${PROTECTED_EXACT[@]}"; do
    if [ "$REL_PATH" = "$protected" ]; then
        BASENAME=$(basename "$protected")
        echo "PROTECTED: '$BASENAME' is a shared governance file."
        echo "Edit requires explicit lead authorization. Record a dependency note instead."
        echo "File: $protected"
        exit 2
    fi
done

exit 0
