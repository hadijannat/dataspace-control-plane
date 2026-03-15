# targets/ci.hcl — CI build targets.
# Platform: linux/amd64 only (no push).
# Cache: GitHub Actions cache backend (type=gha).
# Output: local Docker daemon for test runner consumption.

target "control-api-ci" {
  inherits   = ["control-api"]
  cache-from = ["type=gha,scope=control-api"]
  cache-to   = ["type=gha,mode=max,scope=control-api"]
  output     = ["type=docker"]
}

target "temporal-workers-ci" {
  inherits   = ["temporal-workers"]
  cache-from = ["type=gha,scope=temporal-workers"]
  cache-to   = ["type=gha,mode=max,scope=temporal-workers"]
  output     = ["type=docker"]
}

target "web-console-ci" {
  inherits   = ["web-console"]
  cache-from = ["type=gha,scope=web-console"]
  cache-to   = ["type=gha,mode=max,scope=web-console"]
  output     = ["type=docker"]
}

target "provisioning-agent-ci" {
  inherits   = ["provisioning-agent"]
  cache-from = ["type=gha,scope=provisioning-agent"]
  cache-to   = ["type=gha,mode=max,scope=provisioning-agent"]
  output     = ["type=docker"]
}
