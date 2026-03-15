#!/usr/bin/env bash
# tests/scripts/run_dcp_tck.sh
#
# Runs the Eclipse Dataspace TCK for the DCP protocol against all three SUT actors.
#
# Requirements:
#   - tests/compatibility/dcp-tck/lock.yaml must exist with a tck_tag field
#   - DCP_CREDENTIAL_SERVICE_URL, DCP_ISSUER_URL, DCP_VERIFIER_URL env vars must be set
#   - Java 17+ on PATH
#
# Usage:
#   DCP_CREDENTIAL_SERVICE_URL=http://localhost:8090 \
#   DCP_ISSUER_URL=http://localhost:8091 \
#   DCP_VERIFIER_URL=http://localhost:8092 \
#   bash tests/scripts/run_dcp_tck.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCK_FILE="${REPO_ROOT}/tests/compatibility/dcp-tck/lock.yaml"
CACHE_DIR="${REPO_ROOT}/.tck_cache/dcp"
REPORTS_DIR="${REPO_ROOT}/tests/compatibility/dcp-tck/reports"
CONFIG_DIR="${REPO_ROOT}/tests/compatibility/dcp-tck/config"

# ---------------------------------------------------------------------------
# 1. Check lock file exists
# ---------------------------------------------------------------------------

if [[ ! -f "${LOCK_FILE}" ]]; then
    echo "ERROR: Lock file not found: ${LOCK_FILE}" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Read tck_tag from lock.yaml
# ---------------------------------------------------------------------------

TCK_TAG="$(grep -E '^tck_tag:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"

if [[ -z "${TCK_TAG}" ]]; then
    echo "ERROR: tck_tag not found in ${LOCK_FILE}" >&2
    exit 1
fi

echo "DCP TCK version: ${TCK_TAG}"

# ---------------------------------------------------------------------------
# 3. Download TCK jar if not cached
# ---------------------------------------------------------------------------

mkdir -p "${CACHE_DIR}"
TCK_JAR="${CACHE_DIR}/dcp-tck-runner-${TCK_TAG}.jar"

if [[ ! -f "${TCK_JAR}" ]]; then
    TCK_SOURCE="$(grep -E '^tck_source:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
    DOWNLOAD_URL="${TCK_SOURCE}/releases/download/${TCK_TAG}/dcp-tck-runner-${TCK_TAG}.jar"
    echo "Downloading DCP TCK from: ${DOWNLOAD_URL}"
    curl -fsSL -o "${TCK_JAR}" "${DOWNLOAD_URL}" || {
        echo "ERROR: Failed to download DCP TCK jar." >&2
        exit 1
    }
    echo "Cached at: ${TCK_JAR}"
fi

# ---------------------------------------------------------------------------
# 4. Validate actor env vars
# ---------------------------------------------------------------------------

: "${DCP_CREDENTIAL_SERVICE_URL:?DCP_CREDENTIAL_SERVICE_URL must be set}"
: "${DCP_ISSUER_URL:?DCP_ISSUER_URL must be set}"
: "${DCP_VERIFIER_URL:?DCP_VERIFIER_URL must be set}"

# ---------------------------------------------------------------------------
# 5. Generate actor env files
# ---------------------------------------------------------------------------

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

echo "Actor env files written to ${CONFIG_DIR}"

# ---------------------------------------------------------------------------
# 6. Run TCK jar
# ---------------------------------------------------------------------------

mkdir -p "${REPORTS_DIR}"
JUNIT_REPORT="${REPORTS_DIR}/report.xml"

echo "Running DCP TCK..."
java -jar "${TCK_JAR}" \
    --credential-service-url "${DCP_CREDENTIAL_SERVICE_URL}" \
    --issuer-url "${DCP_ISSUER_URL}" \
    --verifier-url "${DCP_VERIFIER_URL}" \
    --junit-report "${JUNIT_REPORT}"

TCK_EXIT=$?
echo "TCK exit code: ${TCK_EXIT}"
echo "JUnit report: ${JUNIT_REPORT}"
exit ${TCK_EXIT}
