#!/usr/bin/env bash
# tests/compatibility/dsp-tck/scripts/run.sh
# Execute the pinned DSP TCK runner with the generated SUT configuration.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TCK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCK_FILE="${TCK_DIR}/lock.yaml"
CONFIG_DIR="${TCK_DIR}/config"
REPORTS_DIR="${TCK_DIR}/reports"
REPO_ROOT="$(cd "${TCK_DIR}/../../.." && pwd)"
CACHE_DIR="${REPO_ROOT}/.tck_cache/dsp"

TCK_TAG="$(grep -E '^tck_tag:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
TCK_JAR="${CACHE_DIR}/dsp-tck-runner-${TCK_TAG}.jar"
SUT_ENV="${CONFIG_DIR}/sut.env"
JUNIT_REPORT="${REPORTS_DIR}/report.xml"
RAW_LOG="${REPORTS_DIR}/report.log"
COMMAND_LOG="${REPORTS_DIR}/command.txt"

if [[ ! -f "${SUT_ENV}" ]]; then
    echo "ERROR: ${SUT_ENV} not found. Run tests/scripts/run_dsp_tck.sh first." >&2
    exit 1
fi

source "${SUT_ENV}"
: "${DSP_SUT_BASEURL:?DSP_SUT_BASEURL must be set in ${SUT_ENV}}"
: "${DSP_SUT_IDENTITY_URL:?DSP_SUT_IDENTITY_URL must be set in ${SUT_ENV}}"

mkdir -p "${REPORTS_DIR}"

COMMAND=(
    java
    -jar "${TCK_JAR}"
    --sut-base-url "${DSP_SUT_BASEURL}"
    --identity-url "${DSP_SUT_IDENTITY_URL}"
    --junit-report "${JUNIT_REPORT}"
)

printf '%q ' "${COMMAND[@]}" > "${COMMAND_LOG}"
printf '\n' >> "${COMMAND_LOG}"

if [[ "${TCK_DRY_RUN:-0}" == "1" ]]; then
    cat > "${JUNIT_REPORT}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="dsp-tck-dry-run" tests="1" failures="0">
  <properties>
    <property name="mode" value="dry-run" />
    <property name="tck_tag" value="${TCK_TAG}" />
  </properties>
  <testcase classname="compatibility.dsp_tck" name="wrapper_dry_run" />
</testsuite>
EOF
    cat > "${RAW_LOG}" <<EOF
DSP TCK dry-run
tag=${TCK_TAG}
base_url=${DSP_SUT_BASEURL}
identity_url=${DSP_SUT_IDENTITY_URL}
EOF
    echo "DSP TCK dry-run complete: ${JUNIT_REPORT}"
    exit 0
fi

if [[ ! -f "${TCK_JAR}" ]]; then
    echo "TCK jar not found — running fetch_tck.sh first ..."
    bash "${SCRIPT_DIR}/fetch_tck.sh"
fi

echo "Running DSP TCK ${TCK_TAG} against ${DSP_SUT_BASEURL} ..."
("${COMMAND[@]}") 2>&1 | tee "${RAW_LOG}"
TCK_EXIT=${PIPESTATUS[0]}
echo "JUnit report written: ${JUNIT_REPORT}"
exit "${TCK_EXIT}"
