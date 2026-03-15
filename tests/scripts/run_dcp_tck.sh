#!/usr/bin/env bash
# tests/scripts/run_dcp_tck.sh
#
# Repo-root wrapper for the pinned DCP TCK suite.
# Generates actor-specific config/*.env files and delegates to the actor
# wrappers under tests/compatibility/dcp-tck/scripts/.
#
# Set TCK_DRY_RUN=1 to validate orchestration without downloading or running
# the official TCK runner.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TCK_DIR="${REPO_ROOT}/tests/compatibility/dcp-tck"
LOCK_FILE="${TCK_DIR}/lock.yaml"
CONFIG_DIR="${TCK_DIR}/config"
SCRIPTS_DIR="${TCK_DIR}/scripts"

if [[ ! -f "${LOCK_FILE}" ]]; then
    echo "ERROR: lock file not found: ${LOCK_FILE}" >&2
    exit 1
fi

TCK_TAG="$(grep -E '^tck_tag:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
if [[ -z "${TCK_TAG}" ]]; then
    echo "ERROR: tck_tag not found in ${LOCK_FILE}" >&2
    exit 1
fi

: "${DCP_CREDENTIAL_SERVICE_URL:?DCP_CREDENTIAL_SERVICE_URL must be set}"
: "${DCP_ISSUER_URL:?DCP_ISSUER_URL must be set}"
: "${DCP_VERIFIER_URL:?DCP_VERIFIER_URL must be set}"

mkdir -p "${CONFIG_DIR}"

cat > "${CONFIG_DIR}/credential-service.env" <<EOF
DCP_CREDENTIAL_SERVICE_URL=${DCP_CREDENTIAL_SERVICE_URL}
EOF

cat > "${CONFIG_DIR}/issuer.env" <<EOF
DCP_ISSUER_URL=${DCP_ISSUER_URL}
EOF

cat > "${CONFIG_DIR}/verifier.env" <<EOF
DCP_VERIFIER_URL=${DCP_VERIFIER_URL}
EOF

echo "Prepared DCP TCK ${TCK_TAG} actor configs under ${CONFIG_DIR}"

bash "${SCRIPTS_DIR}/run_credential_service.sh"
bash "${SCRIPTS_DIR}/run_issuer.sh"
exec bash "${SCRIPTS_DIR}/run_verifier.sh"
