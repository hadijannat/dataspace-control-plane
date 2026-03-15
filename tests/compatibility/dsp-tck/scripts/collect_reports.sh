#!/usr/bin/env bash
# tests/compatibility/dsp-tck/scripts/collect_reports.sh
# Copies DSP TCK JUnit XML reports and raw logs to $ARTIFACT_DIR.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TCK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPORTS_DIR="${TCK_DIR}/reports"

if [[ -z "${ARTIFACT_DIR:-}" ]]; then
    echo "ARTIFACT_DIR not set — skipping artifact collection"
    exit 0
fi

mkdir -p "${ARTIFACT_DIR}/dsp-tck"

if [[ -d "${REPORTS_DIR}" ]]; then
    count=0
    for report_file in "${REPORTS_DIR}"/*; do
        [[ -f "${report_file}" ]] || continue
        cp "${report_file}" "${ARTIFACT_DIR}/dsp-tck/"
        echo "Copied: ${report_file} → ${ARTIFACT_DIR}/dsp-tck/"
        count=$((count + 1))
    done
    echo "Collected ${count} DSP TCK artifact(s) to ${ARTIFACT_DIR}/dsp-tck/"
else
    echo "No reports directory found: ${REPORTS_DIR}"
fi
