# Docker — Image Builds and Local Composition

## Purpose

`infra/docker/` owns image builds and local or CI container composition. It does not define Kubernetes release behavior and it does not provision shared infrastructure.

Builds are standardized on BuildKit, Buildx, and Bake. Compose is used only for local development and CI-style stack assembly.

## Directory Layout

```text
infra/docker/
├── images/
│   ├── control-api/
│   ├── temporal-workers/
│   ├── web-console/
│   ├── provisioning-agent/
│   └── base/
├── bake/
│   ├── docker-bake.hcl
│   └── targets/
│       ├── apps.hcl
│       ├── ci.hcl
│       └── release.hcl
├── compose/
│   ├── compose.yaml
│   ├── compose.dev.yaml
│   ├── compose.test.yaml
│   └── compose.observability.yaml
└── scripts/
    ├── build.sh
    └── push.sh
```

## Bake Usage

Bake target definitions are loaded explicitly with multiple `-f` flags. Do not rely on `include` in the root HCL file.

Validate the merged Bake model:

```bash
docker buildx bake \
  -f infra/docker/bake/docker-bake.hcl \
  -f infra/docker/bake/targets/apps.hcl \
  -f infra/docker/bake/targets/ci.hcl \
  -f infra/docker/bake/targets/release.hcl \
  --print
```

Local builds:

```bash
./infra/docker/scripts/build.sh
./infra/docker/scripts/build.sh ci
./infra/docker/scripts/build.sh control-api
```

Release builds:

```bash
TAG=0.1.0 \
REGISTRY=ghcr.io/your-org/dataspace-control-plane \
PYTHON_BASE_IMAGE=python:3.12-slim@sha256:... \
NODE_BASE_IMAGE=node:20-alpine@sha256:... \
./infra/docker/scripts/push.sh release
```

## Base Image Contract

Application Dockerfiles accept explicit base image references from Bake:

| Workload | Build arg | Default |
|----------|-----------|---------|
| `control-api` | `PYTHON_BASE_IMAGE` | `python:3.12-slim` |
| `temporal-workers` | `PYTHON_BASE_IMAGE` | `python:3.12-slim` |
| `provisioning-agent` | `PYTHON_BASE_IMAGE` | `python:3.12-slim` |
| `web-console` | `NODE_BASE_IMAGE` | `node:20-alpine` |

Dev and CI can use tagged bases. Release targets should pass digest-pinned base image references.

## Target Groups

| Group | Platforms | Intent |
|-------|-----------|--------|
| `default` | `linux/amd64` | Local developer builds |
| `ci` | `linux/amd64` | CI builds with cache and local Docker output |
| `release` | `linux/amd64`, `linux/arm64` | Multi-platform registry push |

## Release Contract

1. CI builds an image once through Bake.
2. Release builds push immutable images and record their digests.
3. Helm production overlays are updated with `image.digest`.
4. No environment promotes a mutable application tag as the production release artifact.

## Build Secrets

Never pass secrets through Docker `ARG` or `ENV`. Use BuildKit secret or SSH mounts.

```dockerfile
RUN --mount=type=secret,id=npm_token npm install
```

```bash
docker buildx bake \
  -f infra/docker/bake/docker-bake.hcl \
  -f infra/docker/bake/targets/apps.hcl \
  --secret id=npm_token,src=~/.npm-token
```

## Compose

Compose files define local and CI runtime stacks only.

Validate merged Compose models:

```bash
docker compose -f infra/docker/compose/compose.yaml -f infra/docker/compose/compose.dev.yaml config
docker compose -f infra/docker/compose/compose.yaml -f infra/docker/compose/compose.test.yaml config
docker compose -f infra/docker/compose/compose.yaml -f infra/docker/compose/compose.dev.yaml -f infra/docker/compose/compose.observability.yaml config
```

Typical runs:

```bash
docker compose -f infra/docker/compose/compose.yaml -f infra/docker/compose/compose.dev.yaml up
docker compose -f infra/docker/compose/compose.yaml -f infra/docker/compose/compose.dev.yaml -f infra/docker/compose/compose.observability.yaml up
docker compose -f infra/docker/compose/compose.yaml -f infra/docker/compose/compose.test.yaml up -d
```

## Compose Secrets

Runtime secrets are mounted as files under `/run/secrets/<name>`. Keep secret files under `infra/docker/compose/secrets/`, which remains gitignored.

```bash
mkdir -p infra/docker/compose/secrets
echo -n "$(openssl rand -base64 32)" > infra/docker/compose/secrets/postgres_password.txt
echo -n "$(openssl rand -base64 32)" > infra/docker/compose/secrets/keycloak_admin_password.txt
```
