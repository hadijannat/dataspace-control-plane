#!/usr/bin/env bash
# tests/compatibility/dcp-tck/scripts/run_issuer.sh
# Execute the pinned DCP TCK runner for the Issuer actor.

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
ENV_FILE="${CONFIG_DIR}/issuer.env"
JUNIT_REPORT="${REPORTS_DIR}/issuer-report.xml"
RAW_LOG="${REPORTS_DIR}/issuer.log"
COMMAND_LOG="${REPORTS_DIR}/issuer-command.txt"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "ERROR: ${ENV_FILE} not found. Run tests/scripts/run_dcp_tck.sh first." >&2
    exit 1
fi

source "${ENV_FILE}"
: "${DCP_ISSUER_URL:?DCP_ISSUER_URL must be set}"

mkdir -p "${REPORTS_DIR}"

COMMAND=(
    java
    -jar "${TCK_JAR}"
    --actor issuer
    --issuer-url "${DCP_ISSUER_URL}"
    --protocols cip
    --junit-report "${JUNIT_REPORT}"
)

printf '%q ' "${COMMAND[@]}" > "${COMMAND_LOG}"
printf '\n' >> "${COMMAND_LOG}"

if [[ "${TCK_DRY_RUN:-0}" == "1" ]]; then
    cat > "${JUNIT_REPORT}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="dcp-tck-issuer-dry-run" tests="1" failures="0">
  <properties>
    <property name="mode" value="dry-run" />
    <property name="tck_tag" value="${TCK_TAG}" />
    <property name="protocols" value="cip" />
  </properties>
  <testcase classname="compatibility.dcp_tck" name="issuer_wrapper_dry_run" />
</testsuite>
EOF
    cat > "${RAW_LOG}" <<EOF
DCP TCK dry-run
actor=issuer
url=${DCP_ISSUER_URL}
protocols=cip
EOF
    echo "DCP Issuer dry-run complete: ${JUNIT_REPORT}"
    exit 0
fi

if [[ ! -f "${TCK_JAR}" ]]; then
    echo "Fetching DCP TCK jar ..."
    bash "${SCRIPT_DIR}/fetch_tck.sh"
fi

echo "Running DCP TCK (Issuer) against ${DCP_ISSUER_URL} ..."
("${COMMAND[@]}") 2>&1 | tee "${RAW_LOG}"
TCK_EXIT=${PIPESTATUS[0]}
echo "Report written: ${JUNIT_REPORT}"
exit "${TCK_EXIT}"
