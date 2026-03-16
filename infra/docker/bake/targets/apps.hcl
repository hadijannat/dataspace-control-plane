# targets/apps.hcl — Developer local build targets.
# Platform: linux/amd64 only.
# Output: local Docker daemon (default buildx behavior without --push).
# Cache: inline (no external cache backend).

target "control-api" {
  context    = "../../.."  # repository root
  dockerfile = "infra/docker/images/control-api/Dockerfile"
  tags       = ["${REGISTRY}/control-api:${TAG}"]
  platforms  = ["linux/amd64"]
  args = {
    PYTHON_BASE_IMAGE = PYTHON_BASE_IMAGE
  }
}

target "temporal-workers" {
  context    = "../../.."
  dockerfile = "infra/docker/images/temporal-workers/Dockerfile"
  tags       = ["${REGISTRY}/temporal-workers:${TAG}"]
  platforms  = ["linux/amd64"]
  args = {
    PYTHON_BASE_IMAGE = PYTHON_BASE_IMAGE
  }
}

target "web-console" {
  context    = "../../.."
  dockerfile = "infra/docker/images/web-console/Dockerfile"
  tags       = ["${REGISTRY}/web-console:${TAG}"]
  platforms  = ["linux/amd64"]
  args = {
    NODE_BASE_IMAGE = NODE_BASE_IMAGE
  }
}

target "provisioning-agent" {
  context    = "../../.."
  dockerfile = "infra/docker/images/provisioning-agent/Dockerfile"
  tags       = ["${REGISTRY}/provisioning-agent:${TAG}"]
  platforms  = ["linux/amd64"]
  args = {
    PYTHON_BASE_IMAGE = PYTHON_BASE_IMAGE
  }
}
