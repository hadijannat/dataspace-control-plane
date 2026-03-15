#!/usr/bin/env bash
# tests/compatibility/dsp-tck/scripts/fetch_tck.sh
# Downloads the DSP TCK jar from GitHub releases and caches it.
# Verifies sha256 if not PENDING in lock.yaml.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TCK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCK_FILE="${TCK_DIR}/lock.yaml"
REPO_ROOT="$(cd "${TCK_DIR}/../../.." && pwd)"
CACHE_DIR="${REPO_ROOT}/.tck_cache/dsp"

# Read tck_tag from lock.yaml
TCK_TAG="$(grep -E '^tck_tag:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
TCK_SOURCE="$(grep -E '^tck_source:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"
SHA256_EXPECTED="$(grep -E '^sha256:' "${LOCK_FILE}" | awk '{gsub(/"/, "", $2); print $2}')"

if [[ -z "${TCK_TAG}" ]]; then
    echo "ERROR: tck_tag not found in ${LOCK_FILE}" >&2
    exit 1
fi

mkdir -p "${CACHE_DIR}"
TCK_JAR="${CACHE_DIR}/dsp-tck-runner-${TCK_TAG}.jar"

if [[ -f "${TCK_JAR}" ]]; then
    echo "DSP TCK jar already cached: ${TCK_JAR}"
else
    DOWNLOAD_URL="${TCK_SOURCE}/releases/download/${TCK_TAG}/dsp-tck-runner-${TCK_TAG}.jar"
    echo "Downloading DSP TCK ${TCK_TAG} from ${DOWNLOAD_URL} ..."
    curl -fsSL -o "${TCK_JAR}" "${DOWNLOAD_URL}"
    echo "Downloaded: ${TCK_JAR}"
fi

# Verify sha256 if not PENDING
if [[ "${SHA256_EXPECTED}" != "PENDING" && -n "${SHA256_EXPECTED}" ]]; then
    echo "Verifying sha256 ..."
    if command -v sha256sum &>/dev/null; then
        ACTUAL="$(sha256sum "${TCK_JAR}" | awk '{print $1}')"
    else
        ACTUAL="$(shasum -a 256 "${TCK_JAR}" | awk '{print $1}')"
    fi
    if [[ "${ACTUAL}" != "${SHA256_EXPECTED}" ]]; then
        echo "ERROR: sha256 mismatch!" >&2
        echo "  expected: ${SHA256_EXPECTED}" >&2
        echo "  actual:   ${ACTUAL}" >&2
        rm -f "${TCK_JAR}"
        exit 1
    fi
    echo "sha256 OK: ${ACTUAL}"
else
    echo "sha256: PENDING (skipping verification)"
fi

echo "DSP TCK jar ready: ${TCK_JAR}"
