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
#   PYTHON_BASE_DIGEST  sha256 digest to pin the Python base image
#   NODE_BASE_DIGEST    sha256 digest to pin the Node.js base image
#
# Output:
#   .digests/<target>.digest — recorded pushed digests per image
#
# Example:
#   TAG=0.1.0 REGISTRY=ghcr.io/your-org/... PYTHON_BASE_DIGEST=sha256:abc \
#     ./push.sh release
#
# Requirements: docker with buildx plugin + authenticated to REGISTRY

set -euo pipefail

TARGET="${1:-release}"
BAKE_FILE="$(cd "$(dirname "$0")/../bake" && pwd)/docker-bake.hcl"
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

# Build and push
TAG="$TAG" \
REGISTRY="$REGISTRY" \
PYTHON_BASE_DIGEST="${PYTHON_BASE_DIGEST:-}" \
NODE_BASE_DIGEST="${NODE_BASE_DIGEST:-}" \
  docker buildx bake \
    --file "$BAKE_FILE" \
    "$TARGET" \
    --push

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
echo "Use these digests to update Helm values image.tag fields for production deployment."
