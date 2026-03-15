#!/usr/bin/env bash
# tests/compatibility/dsp-tck/scripts/run.sh
# Runs the DSP TCK jar against the SUT.
# Sources config/sut.env for connection parameters.
# Writes JUnit XML to reports/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TCK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCK_FILE="${TCK_DIR}/lock.yaml"
CONFIG_DIR="${TCK_DIR}/config"
REPORTS_DIR="${TCK_DIR}/reports"
REPO_ROOT="$(cd "${TCK_DIR}/../../.." && pwd)"
CACHE_DIR="${REPO_ROOT}/.tck_cache/dsp"

# Read TCK version
TCK_TAG="$(grep -E '^tck_tag:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
TCK_JAR="${CACHE_DIR}/dsp-tck-runner-${TCK_TAG}.jar"

if [[ ! -f "${TCK_JAR}" ]]; then
    echo "TCK jar not found — running fetch_tck.sh first ..."
    bash "${SCRIPT_DIR}/fetch_tck.sh"
fi

# Source SUT environment
SUT_ENV="${CONFIG_DIR}/sut.env"
if [[ ! -f "${SUT_ENV}" ]]; then
    echo "ERROR: ${SUT_ENV} not found. Set DSP_SUT_BASEURL and DSP_SUT_IDENTITY_URL." >&2
    exit 1
fi
source "${SUT_ENV}"

: "${DSP_SUT_BASEURL:?DSP_SUT_BASEURL must be set in ${SUT_ENV}}"
: "${DSP_SUT_IDENTITY_URL:?DSP_SUT_IDENTITY_URL must be set in ${SUT_ENV}}"

mkdir -p "${REPORTS_DIR}"
JUNIT_REPORT="${REPORTS_DIR}/report.xml"

echo "Running DSP TCK ${TCK_TAG} against ${DSP_SUT_BASEURL} ..."
java -jar "${TCK_JAR}" \
    --sut-base-url "${DSP_SUT_BASEURL}" \
    --identity-url "${DSP_SUT_IDENTITY_URL}" \
    --junit-report "${JUNIT_REPORT}"

echo "JUnit report written: ${JUNIT_REPORT}"
