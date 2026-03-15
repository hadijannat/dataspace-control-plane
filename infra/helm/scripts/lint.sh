#!/usr/bin/env bash
# lint.sh — Run helm lint on every chart and helm template with each env overlay.
# Exits 1 on any failure.
#
# Usage: ./infra/helm/scripts/lint.sh
# Requirements: helm >= 3.14

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CHARTS_DIR="$REPO_ROOT/infra/helm/charts"
VALUES_DIR="$REPO_ROOT/infra/helm/values"
ENVS=(dev staging prod-eu)
CHARTS=(control-api temporal-workers web-console provisioning-agent platform)

PASS=0
FAIL=0

check() {
  local label="$1"
  shift
  if "$@" > /dev/null 2>&1; then
    echo "  [PASS] $label"
    ((PASS++)) || true
  else
    echo "  [FAIL] $label"
    echo "         Command: $*"
    "$@" || true
    ((FAIL++)) || true
  fi
}

echo "============================================================"
echo " Helm Chart Lint Gate"
echo " Charts dir: $CHARTS_DIR"
echo " Envs:       ${ENVS[*]}"
echo "============================================================"

# Step 1: helm lint each chart with default values
echo ""
echo "--- Step 1: helm lint (default values) ---"
for chart in "${CHARTS[@]}"; do
  echo "Chart: $chart"
  check "helm lint $chart" helm lint "$CHARTS_DIR/$chart"
done

# Step 2: helm template with each env overlay
echo ""
echo "--- Step 2: helm template (env overlays) ---"
for chart in "${CHARTS[@]}"; do
  for env in "${ENVS[@]}"; do
    values_file="$VALUES_DIR/$env/$chart.yaml"
    if [[ -f "$values_file" ]]; then
      echo "Chart: $chart | Env: $env"
      check "helm template $chart [$env]" \
        helm template "$chart" "$CHARTS_DIR/$chart" -f "$values_file"
    else
      echo "  [SKIP] $chart/$env — no overlay at $values_file"
    fi
  done
done

# Step 3: Validate that prod-eu tags are sha256 digests
echo ""
echo "--- Step 3: prod-eu digest check ---"
for chart in "${CHARTS[@]}"; do
  values_file="$VALUES_DIR/prod-eu/$chart.yaml"
  if [[ -f "$values_file" ]]; then
    # Check for mutable tags in prod-eu overlays
    # Allow sha256 digests and REPLACE_WITH_REAL_DIGEST placeholders (CI enforces replacement)
    if grep -E '^\s+tag:' "$values_file" | grep -qvE '(sha256:[a-f0-9]{64}|REPLACE_WITH_REAL_DIGEST)'; then
      echo "  [FAIL] $chart prod-eu overlay contains mutable image tag — must be sha256 digest"
      ((FAIL++)) || true
    else
      echo "  [PASS] $chart prod-eu tag format OK"
      ((PASS++)) || true
    fi
  fi
done

echo ""
echo "============================================================"
echo " Results: $PASS passed, $FAIL failed"
echo "============================================================"

if [[ "$FAIL" -gt 0 ]]; then
  echo "LINT FAILED"
  exit 1
fi

echo "LINT PASSED"
exit 0
