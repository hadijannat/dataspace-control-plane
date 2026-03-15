#!/usr/bin/env bash
# build.sh — Wrapper for docker buildx bake.
#
# Usage:
#   ./infra/docker/scripts/build.sh [<group|target>] [--tag <tag>] [--push]
#
# Environment variables:
#   TAG      Image tag (default: dev)
#   REGISTRY Image registry prefix (default: ghcr.io/your-org/dataspace-control-plane)
#   PUSH     Set to "true" to push after build (default: false)
#
# Examples:
#   ./build.sh                        # build all default targets
#   ./build.sh ci                     # build CI group
#   ./build.sh control-api            # build single target
#   TAG=0.1.0 PUSH=true ./build.sh release  # release build + push
#
# Requirements: docker with buildx plugin (Docker Engine 23+)

set -euo pipefail

BAKE_DIR="$(cd "$(dirname "$0")/../bake" && pwd)"
BAKE_FILES=(
  "$BAKE_DIR/docker-bake.hcl"
  "$BAKE_DIR/targets/apps.hcl"
  "$BAKE_DIR/targets/ci.hcl"
  "$BAKE_DIR/targets/release.hcl"
)

TARGET="${1:-default}"
TAG="${TAG:-dev}"
REGISTRY="${REGISTRY:-ghcr.io/your-org/dataspace-control-plane}"
PUSH="${PUSH:-false}"

echo "============================================================"
echo " Docker Buildx Bake"
echo " Bake files:"
for file in "${BAKE_FILES[@]}"; do
  echo "   - $file"
done
echo " Target:    $TARGET"
echo " Tag:       $TAG"
echo " Registry:  $REGISTRY"
echo " Push:      $PUSH"
echo "============================================================"
echo ""

ARGS=()

for file in "${BAKE_FILES[@]}"; do
  ARGS+=(--file "$file")
done

if [[ "$PUSH" == "true" ]]; then
  ARGS+=(--push)
fi

ARGS+=("$TARGET")

TAG="$TAG" REGISTRY="$REGISTRY" docker buildx bake "${ARGS[@]}"

echo ""
echo "Build complete."
