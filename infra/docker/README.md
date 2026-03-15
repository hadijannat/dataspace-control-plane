# Docker — Image Builds and Local Composition

## Build System

**Builder**: Docker BuildKit + Buildx (default in Docker Engine 23+).

**Build entrypoint**: `docker buildx bake` — never invoke `docker build` directly in CI. The bake file provides reproducible, multi-target, multi-platform builds with unified cache management.

```bash
# Build all default targets (linux/amd64, local)
docker buildx bake --file infra/docker/bake/docker-bake.hcl

# Validate bake config (no build)
docker buildx bake --file infra/docker/bake/docker-bake.hcl --print

# Build and push release targets (multi-platform)
TAG=sha256:abc123 docker buildx bake --file infra/docker/bake/docker-bake.hcl release
```

## Directory Layout

```
infra/docker/
├── images/
│   ├── control-api/        # Multi-stage Python FastAPI Dockerfile
│   ├── temporal-workers/   # Multi-stage Python Temporal worker Dockerfile
│   ├── web-console/        # Multi-stage Next.js Dockerfile
│   ├── provisioning-agent/ # Multi-stage Python provisioning agent Dockerfile
│   └── base/
│       ├── python-runtime.Dockerfile  # Shared Python base
│       └── node-build.Dockerfile      # Shared Node.js build base
├── bake/
│   ├── docker-bake.hcl          # Root bake file (groups, variables, includes)
│   └── targets/
│       ├── apps.hcl             # Dev local targets
│       ├── ci.hcl               # CI targets (GHA cache, local output)
│       └── release.hcl          # Release targets (multi-platform, push)
├── compose/
│   ├── compose.yaml             # Base services (Postgres, Temporal, Keycloak, Vault)
│   ├── compose.dev.yaml         # Dev overlay (app services with hot-reload)
│   ├── compose.test.yaml        # CI integration test overlay
│   └── compose.observability.yaml # OTel + Prometheus + Grafana + Loki
└── scripts/
    ├── build.sh                 # Build wrapper
    └── push.sh                  # Push and record digest
```

## Base Images

| Image | Base | Pinned |
|-------|------|--------|
| control-api | python:3.12-slim | Semver in dev, digest in release |
| temporal-workers | python:3.12-slim | Semver in dev, digest in release |
| web-console | node:20-alpine | Semver in dev, digest in release |
| provisioning-agent | python:3.12-slim | Semver in dev, digest in release |

Pin base image digests using `PYTHON_BASE_DIGEST` and `NODE_BASE_DIGEST` Bake variables in release targets.

## Secrets

**Never pass secrets via ARG or ENV.** Use BuildKit secret mounts:

```dockerfile
# In Dockerfile:
RUN --mount=type=secret,id=npm_token npm install
```

```bash
# At build time:
docker buildx bake --secret id=npm_token,src=~/.npm-token
```

## Platforms

| Target group | Platforms |
|-------------|-----------|
| `default` / `ci` | linux/amd64 |
| `release` | linux/amd64, linux/arm64 |

## Release Contract

1. CI calls `docker buildx bake ci` — builds and caches, no push
2. On merge to main: CI calls `docker buildx bake release` — pushes with digest
3. Digest is captured and injected into Helm values for the target environment
4. Helm upgrade references the digest (`sha256:...`), never a mutable tag
5. Never promote by reusing mutable tags between environments

## Compose Profiles

| Profile | Use case |
|---------|----------|
| (none) | Core infrastructure: Postgres, Keycloak, Vault, Temporal |
| `--profile kafka` | Adds Kafka + Zookeeper |

```bash
# Start core + app services
docker compose -f compose/compose.yaml -f compose/compose.dev.yaml up

# Start with observability
docker compose -f compose/compose.yaml -f compose/compose.dev.yaml -f compose/compose.observability.yaml up

# Start CI test stack
docker compose -f compose/compose.yaml -f compose/compose.test.yaml up -d
```

## Secrets in Compose

Compose secrets are mounted as files under `/run/secrets/<name>`. Applications must read from the file, not from environment variables.

Create secret files before starting the stack:

```bash
mkdir -p infra/docker/compose/secrets
echo -n "$(openssl rand -base64 32)" > infra/docker/compose/secrets/postgres_password.txt
echo -n "$(openssl rand -base64 32)" > infra/docker/compose/secrets/keycloak_admin_password.txt
```

The `secrets/` directory is gitignored. Never commit secret files.
