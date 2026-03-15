#!/usr/bin/env bash
# tests/scripts/run_dsp_tck.sh
#
# Runs the Eclipse Dataspace TCK for the DSP protocol against the SUT.
#
# Requirements:
#   - tests/compatibility/dsp-tck/lock.yaml must exist with a tck_tag field
#   - DSP_SUT_BASEURL env var must be set
#   - DSP_SUT_IDENTITY_URL env var must be set
#   - Java 17+ on PATH (for TCK jar)
#
# Usage:
#   DSP_SUT_BASEURL=http://localhost:8080 DSP_SUT_IDENTITY_URL=http://localhost:8081 \
#   bash tests/scripts/run_dsp_tck.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCK_FILE="${REPO_ROOT}/tests/compatibility/dsp-tck/lock.yaml"
CACHE_DIR="${REPO_ROOT}/.tck_cache/dsp"
REPORTS_DIR="${REPO_ROOT}/tests/compatibility/dsp-tck/reports"
CONFIG_DIR="${REPO_ROOT}/tests/compatibility/dsp-tck/config"

# ---------------------------------------------------------------------------
# 1. Check lock file exists
# ---------------------------------------------------------------------------

if [[ ! -f "${LOCK_FILE}" ]]; then
    echo "ERROR: Lock file not found: ${LOCK_FILE}" >&2
    echo "Create it with tck_tag and tck_source fields before running." >&2
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

echo "DSP TCK version: ${TCK_TAG}"

# ---------------------------------------------------------------------------
# 3. Download TCK jar if not cached
# ---------------------------------------------------------------------------

mkdir -p "${CACHE_DIR}"
TCK_JAR="${CACHE_DIR}/dsp-tck-runner-${TCK_TAG}.jar"

if [[ ! -f "${TCK_JAR}" ]]; then
    TCK_SOURCE="$(grep -E '^tck_source:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
    if [[ -z "${TCK_SOURCE}" ]]; then
        echo "ERROR: tck_source not in lock.yaml" >&2
        exit 1
    fi
    DOWNLOAD_URL="${TCK_SOURCE}/releases/download/${TCK_TAG}/dsp-tck-runner-${TCK_TAG}.jar"
    echo "Downloading DSP TCK from: ${DOWNLOAD_URL}"
    curl -fsSL -o "${TCK_JAR}" "${DOWNLOAD_URL}" || {
        echo "ERROR: Failed to download TCK jar. Check tck_tag and tck_source." >&2
        exit 1
    }
    echo "Cached at: ${TCK_JAR}"
fi

# ---------------------------------------------------------------------------
# 4. Generate sut.env from environment variables
# ---------------------------------------------------------------------------

mkdir -p "${CONFIG_DIR}"
SUT_ENV="${CONFIG_DIR}/sut.env"

: "${DSP_SUT_BASEURL:?DSP_SUT_BASEURL must be set}"
: "${DSP_SUT_IDENTITY_URL:?DSP_SUT_IDENTITY_URL must be set}"

cat > "${SUT_ENV}" <<EOF
DSP_SUT_BASEURL=${DSP_SUT_BASEURL}
DSP_SUT_IDENTITY_URL=${DSP_SUT_IDENTITY_URL}
EOF

echo "SUT env written: ${SUT_ENV}"

# ---------------------------------------------------------------------------
# 5. Run TCK jar
# ---------------------------------------------------------------------------

mkdir -p "${REPORTS_DIR}"
JUNIT_REPORT="${REPORTS_DIR}/report.xml"

echo "Running DSP TCK against ${DSP_SUT_BASEURL} ..."
java -jar "${TCK_JAR}" \
    --sut-base-url "${DSP_SUT_BASEURL}" \
    --identity-url "${DSP_SUT_IDENTITY_URL}" \
    --junit-report "${JUNIT_REPORT}"

TCK_EXIT=$?
echo "TCK exit code: ${TCK_EXIT}"
echo "JUnit report: ${JUNIT_REPORT}"
exit ${TCK_EXIT}
