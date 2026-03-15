# docker-bake.hcl — Root bake file for the dataspace control-plane.
#
# Usage:
#   docker buildx bake -f infra/docker/bake/docker-bake.hcl -f infra/docker/bake/targets/apps.hcl -f infra/docker/bake/targets/ci.hcl -f infra/docker/bake/targets/release.hcl default
#   docker buildx bake -f infra/docker/bake/docker-bake.hcl -f infra/docker/bake/targets/apps.hcl -f infra/docker/bake/targets/ci.hcl -f infra/docker/bake/targets/release.hcl --print
#
# Variables (override via env or --set):
#   TAG=<tag>                 Image tag (default: dev)
#   REGISTRY=<url>            Registry prefix (default: ghcr.io/your-org/dataspace-control-plane)
#   PYTHON_BASE_IMAGE=<ref>   Base image ref for Python services
#   NODE_BASE_IMAGE=<ref>     Base image ref for Node services
#
# Release pinning:
#   Set PYTHON_BASE_IMAGE / NODE_BASE_IMAGE to digest-pinned refs during release builds.

variable "REGISTRY" {
  default = "ghcr.io/your-org/dataspace-control-plane"
}

variable "TAG" {
  default = "dev"
}

variable "PYTHON_BASE_IMAGE" {
  default = "python:3.12-slim"
}

variable "NODE_BASE_IMAGE" {
  default = "node:20-alpine"
}

# Default group: builds all app images for local dev (linux/amd64 only)
group "default" {
  targets = ["control-api", "temporal-workers", "web-console", "provisioning-agent"]
}

# CI group: adds GHA cache, outputs to local Docker daemon
group "ci" {
  targets = ["control-api-ci", "temporal-workers-ci", "web-console-ci", "provisioning-agent-ci"]
}

# Release group: multi-platform builds, push to registry
group "release" {
  targets = ["control-api-release", "temporal-workers-release", "web-console-release", "provisioning-agent-release"]
}

# Target definitions are loaded explicitly by infra/docker/scripts/build.sh,
# infra/docker/scripts/push.sh, and the documented verification commands.
