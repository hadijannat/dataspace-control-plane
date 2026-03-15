# docker-bake.hcl — Root bake file for the dataspace control-plane.
#
# Usage:
#   docker buildx bake                        # build all default targets
#   docker buildx bake --print                # validate config without building
#   docker buildx bake ci                     # build CI targets (local, GHA cache)
#   docker buildx bake release                # build release targets (multi-platform, push)
#   docker buildx bake control-api            # build single target
#
# Variables (override via env or --set):
#   TAG=<tag>          Image tag (default: dev)
#   REGISTRY=<url>     Registry prefix (default: ghcr.io/your-org/dataspace-control-plane)
#
# Release pinning:
#   PYTHON_BASE_DIGEST=sha256:<digest>  Pins python base image for release builds
#   NODE_BASE_DIGEST=sha256:<digest>    Pins node base image for release builds

variable "REGISTRY" {
  default = "ghcr.io/your-org/dataspace-control-plane"
}

variable "TAG" {
  default = "dev"
}

variable "PYTHON_VERSION" {
  default = "3.12"
}

variable "NODE_VERSION" {
  default = "20"
}

# Base image digests — set in release builds via CI to pin exact base images.
# Leave empty for dev builds (uses floating tag).
variable "PYTHON_BASE_DIGEST" {
  default = ""
}

variable "NODE_BASE_DIGEST" {
  default = ""
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

# Import sub-target definitions
# Paths are relative to this bake file's location (infra/docker/bake/)
include {
  path = ["targets/apps.hcl", "targets/ci.hcl", "targets/release.hcl"]
}
