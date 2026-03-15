#!/usr/bin/env bash
# tests/scripts/run_dsp_tck.sh
#
# Repo-root wrapper for the pinned DSP TCK suite.
# Generates config/sut.env from the target environment and delegates execution
# to tests/compatibility/dsp-tck/scripts/run.sh.
#
# Set TCK_DRY_RUN=1 to validate wrapper wiring without downloading or running
# the official TCK runner.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TCK_DIR="${REPO_ROOT}/tests/compatibility/dsp-tck"
LOCK_FILE="${TCK_DIR}/lock.yaml"
CONFIG_DIR="${TCK_DIR}/config"
RUNNER="${TCK_DIR}/scripts/run.sh"

if [[ ! -f "${LOCK_FILE}" ]]; then
    echo "ERROR: lock file not found: ${LOCK_FILE}" >&2
    exit 1
fi

TCK_TAG="$(grep -E '^tck_tag:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
if [[ -z "${TCK_TAG}" ]]; then
    echo "ERROR: tck_tag not found in ${LOCK_FILE}" >&2
    exit 1
fi

: "${DSP_SUT_BASEURL:?DSP_SUT_BASEURL must be set}"
: "${DSP_SUT_IDENTITY_URL:?DSP_SUT_IDENTITY_URL must be set}"

mkdir -p "${CONFIG_DIR}"
cat > "${CONFIG_DIR}/sut.env" <<EOF
DSP_SUT_BASEURL=${DSP_SUT_BASEURL}
DSP_SUT_IDENTITY_URL=${DSP_SUT_IDENTITY_URL}
EOF

echo "Prepared DSP TCK ${TCK_TAG} config: ${CONFIG_DIR}/sut.env"
exec bash "${RUNNER}"
