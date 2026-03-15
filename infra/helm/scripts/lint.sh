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

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 127
  fi
}

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

require_command helm
require_command python3

if ! python3 -c "import yaml" >/dev/null 2>&1; then
  echo "Required Python module not found: pyyaml (import yaml)" >&2
  exit 127
fi

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
      echo "  [FAIL] Missing required overlay: $values_file"
      ((FAIL++)) || true
    fi
  done
done

# Step 3: Validate that prod-eu image configuration uses digest fields only
echo ""
echo "--- Step 3: prod-eu digest check ---"
for chart in "${CHARTS[@]}"; do
  values_file="$VALUES_DIR/prod-eu/$chart.yaml"
  if [[ -f "$values_file" ]]; then
    if python3 - "$chart" "$values_file" <<'PY'
import sys
import yaml

chart = sys.argv[1]
values_path = sys.argv[2]

with open(values_path, "r", encoding="utf-8") as handle:
    data = yaml.safe_load(handle) or {}

digest_pattern = "sha256:"

def check_image(name, image):
    if not isinstance(image, dict):
        raise SystemExit(f"{name}: image block missing")
    if "tag" in image:
        raise SystemExit(f"{name}: image.tag is not allowed in prod overlays")
    digest = image.get("digest")
    if not isinstance(digest, str) or not digest.startswith(digest_pattern):
        raise SystemExit(f"{name}: image.digest must be set to a sha256 digest")

if chart == "platform":
    for component in ("control-api", "temporal-workers", "web-console", "provisioning-agent"):
        component_values = data.get(component, {})
        if component_values.get("enabled", False):
            check_image(component, component_values.get("image"))
else:
    check_image(chart, data.get("image"))
PY
    then
      echo "  [PASS] $chart prod-eu digest configuration OK"
      ((PASS++)) || true
    else
      echo "  [FAIL] $chart prod-eu overlay must use image.digest only"
      ((FAIL++)) || true
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
