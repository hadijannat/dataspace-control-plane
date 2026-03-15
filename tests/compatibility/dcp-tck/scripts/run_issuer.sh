#!/usr/bin/env bash
# tests/compatibility/dcp-tck/scripts/run_issuer.sh
# Runs the DCP TCK against the Issuer actor.
# Sources config/issuer.env for connection parameters.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TCK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCK_FILE="${TCK_DIR}/lock.yaml"
CONFIG_DIR="${TCK_DIR}/config"
REPORTS_DIR="${TCK_DIR}/reports"
REPO_ROOT="$(cd "${TCK_DIR}/../../.." && pwd)"
CACHE_DIR="${REPO_ROOT}/.tck_cache/dcp"

TCK_TAG="$(grep -E '^tck_tag:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
TCK_JAR="${CACHE_DIR}/dcp-tck-runner-${TCK_TAG}.jar"

if [[ ! -f "${TCK_JAR}" ]]; then
    echo "Fetching DCP TCK jar ..."
    bash "${SCRIPT_DIR}/fetch_tck.sh"
fi

ENV_FILE="${CONFIG_DIR}/issuer.env"
if [[ ! -f "${ENV_FILE}" ]]; then
    echo "ERROR: ${ENV_FILE} not found. Set DCP_ISSUER_URL." >&2
    exit 1
fi
source "${ENV_FILE}"
: "${DCP_ISSUER_URL:?DCP_ISSUER_URL must be set}"

mkdir -p "${REPORTS_DIR}"
JUNIT_REPORT="${REPORTS_DIR}/issuer-report.xml"

echo "Running DCP TCK (Issuer) against ${DCP_ISSUER_URL} ..."
java -jar "${TCK_JAR}" \
    --actor issuer \
    --issuer-url "${DCP_ISSUER_URL}" \
    --protocols cip \
    --junit-report "${JUNIT_REPORT}"

echo "Report written: ${JUNIT_REPORT}"
