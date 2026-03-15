#!/usr/bin/env bash
# push.sh — Build release targets and push to registry, recording digests.
#
# Usage:
#   TAG=<semver-or-digest> REGISTRY=<registry> ./infra/docker/scripts/push.sh [<target-group>]
#
# Required environment variables:
#   TAG      Image tag — should be a semver or sha256 digest for release
#   REGISTRY Image registry prefix
#
# Optional:
#   PYTHON_BASE_IMAGE   digest-pinned base image ref for Python services
#   NODE_BASE_IMAGE     digest-pinned base image ref for the web console
#
# Output:
#   .digests/<target>.digest — recorded pushed digests per image
#
# Example:
#   TAG=0.1.0 REGISTRY=ghcr.io/your-org/... \
#   PYTHON_BASE_IMAGE=python:3.12-slim@sha256:abc \
#     ./push.sh release
#
# Requirements: docker with buildx plugin + authenticated to REGISTRY

set -euo pipefail

TARGET="${1:-release}"
BAKE_DIR="$(cd "$(dirname "$0")/../bake" && pwd)"
BAKE_FILES=(
  "$BAKE_DIR/docker-bake.hcl"
  "$BAKE_DIR/targets/apps.hcl"
  "$BAKE_DIR/targets/ci.hcl"
  "$BAKE_DIR/targets/release.hcl"
)
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DIGEST_DIR="$REPO_ROOT/.digests"

# Validate required env vars
: "${TAG:?TAG must be set (e.g. TAG=0.1.0)}"
: "${REGISTRY:?REGISTRY must be set (e.g. REGISTRY=ghcr.io/your-org/...)}"

echo "============================================================"
echo " Docker Push — Release Build"
echo " Target:    $TARGET"
echo " Tag:       $TAG"
echo " Registry:  $REGISTRY"
echo "============================================================"
echo ""

mkdir -p "$DIGEST_DIR"

ENV_VARS=(
  "TAG=$TAG"
  "REGISTRY=$REGISTRY"
)

if [[ -n "${PYTHON_BASE_IMAGE:-}" ]]; then
  ENV_VARS+=("PYTHON_BASE_IMAGE=$PYTHON_BASE_IMAGE")
fi

if [[ -n "${NODE_BASE_IMAGE:-}" ]]; then
  ENV_VARS+=("NODE_BASE_IMAGE=$NODE_BASE_IMAGE")
fi

# Build and push
env "${ENV_VARS[@]}" docker buildx bake \
  --file "${BAKE_FILES[0]}" \
  --file "${BAKE_FILES[1]}" \
  --file "${BAKE_FILES[2]}" \
  --file "${BAKE_FILES[3]}" \
  --push \
  "$TARGET"

echo ""
echo "Push complete."
echo ""

# Record pushed image references for Helm value injection
# In CI, inspect each image's digest and write to .digests/
IMAGES=(control-api temporal-workers web-console provisioning-agent)

echo "Recording image digests..."
for img in "${IMAGES[@]}"; do
  ref="$REGISTRY/$img:$TAG"
  digest=$(docker buildx imagetools inspect "$ref" --format '{{json .Manifest.Digest}}' 2>/dev/null | tr -d '"' || echo "unknown")
  echo "  $img: $digest"
  echo "$digest" > "$DIGEST_DIR/$img.digest"
done

echo ""
echo "Digests recorded in $DIGEST_DIR"
echo "Use these digests to update Helm values image.digest fields for production deployment."
