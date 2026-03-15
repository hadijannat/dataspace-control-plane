#!/usr/bin/env bash
# tests/compatibility/dsp-tck/scripts/collect_reports.sh
# Copies DSP TCK JUnit XML reports to $ARTIFACT_DIR.

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
    for xml_file in "${REPORTS_DIR}"/*.xml; do
        [[ -f "${xml_file}" ]] || continue
        cp "${xml_file}" "${ARTIFACT_DIR}/dsp-tck/"
        echo "Copied: ${xml_file} → ${ARTIFACT_DIR}/dsp-tck/"
        count=$((count + 1))
    done
    echo "Collected ${count} DSP TCK report(s) to ${ARTIFACT_DIR}/dsp-tck/"
else
    echo "No reports directory found: ${REPORTS_DIR}"
fi
