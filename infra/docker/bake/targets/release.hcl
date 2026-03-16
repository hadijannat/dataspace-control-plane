# targets/release.hcl — Release build targets.
# Platforms: linux/amd64 + linux/arm64 (multi-platform).
# Output: type=registry (push to registry immediately after build).
# Cache: registry cache backend for persistent layer reuse.
#
# REQUIREMENTS:
#   - REGISTRY env var must be set to the target registry
#   - TAG env var should be a semantic version or sha256 digest (not 'dev')
#   - Registry credentials must be configured (docker login or DOCKER_AUTH_CONFIG)
#
# Base image pinning:
#   Set PYTHON_BASE_IMAGE and NODE_BASE_IMAGE to digest-pinned refs
#   (for example python:3.12-slim@sha256:...).
#
# Example:
#   TAG=0.1.0 REGISTRY=ghcr.io/your-org/... \
#     PYTHON_BASE_IMAGE=python:3.12-slim@sha256:abc123... \
#     docker buildx bake release

target "control-api-release" {
  inherits   = ["control-api"]
  platforms  = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=registry,ref=${REGISTRY}/control-api:buildcache"]
  cache-to   = ["type=registry,ref=${REGISTRY}/control-api:buildcache,mode=max"]
  output     = ["type=registry"]
  args = {
    PYTHON_BASE_IMAGE = PYTHON_BASE_IMAGE
  }
}

target "temporal-workers-release" {
  inherits   = ["temporal-workers"]
  platforms  = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=registry,ref=${REGISTRY}/temporal-workers:buildcache"]
  cache-to   = ["type=registry,ref=${REGISTRY}/temporal-workers:buildcache,mode=max"]
  output     = ["type=registry"]
  args = {
    PYTHON_BASE_IMAGE = PYTHON_BASE_IMAGE
  }
}

target "web-console-release" {
  inherits   = ["web-console"]
  platforms  = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=registry,ref=${REGISTRY}/web-console:buildcache"]
  cache-to   = ["type=registry,ref=${REGISTRY}/web-console:buildcache,mode=max"]
  output     = ["type=registry"]
  args = {
    NODE_BASE_IMAGE = NODE_BASE_IMAGE
  }
}

target "provisioning-agent-release" {
  inherits   = ["provisioning-agent"]
  platforms  = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=registry,ref=${REGISTRY}/provisioning-agent:buildcache"]
  cache-to   = ["type=registry,ref=${REGISTRY}/provisioning-agent:buildcache,mode=max"]
  output     = ["type=registry"]
  args = {
    PYTHON_BASE_IMAGE = PYTHON_BASE_IMAGE
  }
}
