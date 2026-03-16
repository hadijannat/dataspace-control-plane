#!/usr/bin/env bash
# render.sh — Render a helm chart with an env overlay and write to a file.
#
# Usage:
#   ./infra/helm/scripts/render.sh --chart <name> --env <dev|staging|prod-eu>
#
# Options:
#   --chart   Chart name (control-api, temporal-workers, web-console, provisioning-agent, platform)
#   --env     Environment (dev, staging, prod-eu)
#
# Output:
#   infra/helm/rendered/<env>/<chart>.yaml
#
# Requirements: helm >= 3.14

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CHARTS_DIR="$REPO_ROOT/infra/helm/charts"
VALUES_DIR="$REPO_ROOT/infra/helm/values"
RENDERED_DIR="$REPO_ROOT/infra/helm/rendered"

if ! command -v helm >/dev/null 2>&1; then
  echo "Error: helm is required but was not found in PATH" >&2
  exit 127
fi

CHART=""
ENV=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --chart)
      CHART="$2"
      shift 2
      ;;
    --env)
      ENV="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 --chart <name> --env <dev|staging|prod-eu>" >&2
      exit 1
      ;;
  esac
done

# Validate required arguments
if [[ -z "$CHART" ]]; then
  echo "Error: --chart is required" >&2
  exit 1
fi

if [[ -z "$ENV" ]]; then
  echo "Error: --env is required" >&2
  exit 1
fi

CHART_DIR="$CHARTS_DIR/$CHART"
VALUES_FILE="$VALUES_DIR/$ENV/$CHART.yaml"
OUTPUT_DIR="$RENDERED_DIR/$ENV"
OUTPUT_FILE="$OUTPUT_DIR/$CHART.yaml"

# Validate chart directory exists
if [[ ! -d "$CHART_DIR" ]]; then
  echo "Error: chart directory not found: $CHART_DIR" >&2
  exit 1
fi

# Validate values overlay exists
if [[ ! -f "$VALUES_FILE" ]]; then
  echo "Error: values overlay not found: $VALUES_FILE" >&2
  exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Rendering chart: $CHART"
echo "  Environment:  $ENV"
echo "  Chart dir:    $CHART_DIR"
echo "  Values file:  $VALUES_FILE"
echo "  Output file:  $OUTPUT_FILE"
echo ""

helm template "$CHART" "$CHART_DIR" -f "$VALUES_FILE" > "$OUTPUT_FILE"

echo "Rendered successfully: $OUTPUT_FILE"
echo "Lines: $(wc -l < "$OUTPUT_FILE")"
