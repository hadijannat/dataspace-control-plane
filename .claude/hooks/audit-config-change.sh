#!/usr/bin/env bash
# ConfigChange hook: appends timestamped config change events to audit log.
# Always exits 0.
set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
AUDIT_LOG="$REPO_ROOT/.claude/config-audit.log"

# Read full stdin
PAYLOAD=$(cat)

# ISO8601 timestamp
TIMESTAMP=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat())")

# Append to audit log (create if absent)
echo "[$TIMESTAMP] ConfigChange: $PAYLOAD" >> "$AUDIT_LOG"

exit 0
