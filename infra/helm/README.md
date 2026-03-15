# Helm Chart Library — Dataspace Control Plane

## Purpose

This directory contains Helm charts for packaging and releasing all workloads of the dataspace control-plane monorepo. Charts are thin delivery artifacts: they reference container images, wire environment variables from ConfigMaps and external secret references, and configure Kubernetes primitives (Deployments, Services, HPAs, Ingresses).

No business logic, domain rules, or workflow definitions live here.

## Charts

| Chart | Description |
|-------|-------------|
| `platform` | Umbrella chart — composes all workloads; use this in production releases |
| `control-api` | FastAPI REST control-api service |
| `temporal-workers` | Temporal workflow worker fleet |
| `web-console` | Next.js web UI |
| `provisioning-agent` | Automated tenant and connector provisioning agent |

## Usage

### Lint a single chart

```bash
helm lint infra/helm/charts/control-api
helm lint infra/helm/charts/temporal-workers
helm lint infra/helm/charts/web-console
helm lint infra/helm/charts/provisioning-agent
helm lint infra/helm/charts/platform
```

### Render templates with environment overlay

```bash
helm template control-api infra/helm/charts/control-api \
  -f infra/helm/values/dev/control-api.yaml

helm template platform infra/helm/charts/platform \
  -f infra/helm/values/prod-eu/platform.yaml
```

### Use the render script

```bash
# Render a specific chart+env combination
./infra/helm/scripts/render.sh --chart control-api --env dev

# Output written to infra/helm/rendered/dev/control-api.yaml
```

### Install or upgrade a release

```bash
helm upgrade --install control-api infra/helm/charts/control-api \
  --namespace dataspace \
  --create-namespace \
  -f infra/helm/values/prod-eu/control-api.yaml
```

## Directory Layout

```
infra/helm/
├── charts/
│   ├── platform/              # Umbrella chart
│   ├── control-api/
│   │   ├── Chart.yaml
│   │   ├── values.yaml        # Default values (safe, non-secret)
│   │   ├── values.schema.json # JSON Schema validation (Helm --validate)
│   │   ├── README.md
│   │   └── templates/
│   ├── temporal-workers/
│   ├── web-console/
│   └── provisioning-agent/
├── values/
│   ├── dev/                   # Dev environment overlays
│   ├── staging/               # Staging environment overlays
│   └── prod-eu/               # Production EU overlays
├── scripts/
│   ├── lint.sh                # Lint all charts with all env overlays
│   └── render.sh              # Render chart+env to file
└── rendered/                  # Git-ignored rendered manifests
```

## CI Gates

1. **helm lint** — each chart must pass `helm lint` with no errors
2. **helm template** — each chart rendered with each env overlay must succeed
3. **Schema validation** — `helm template --validate` catches values.schema.json violations
4. **Digest/tag check** — prod-eu overlays must use `sha256:` digest format in `image.tag`; CI fails on mutable tags in production overlays

The lint script (`scripts/lint.sh`) runs all of these gates and exits 1 on any failure.

## Secrets Policy

**Never** commit secrets, tokens, passwords, or private key material in any values file.

Values files carry only:
- K8s Secret **names** (e.g. `control-api-postgres`) — the ExternalSecret or SealedSecret object creates the actual Secret
- ConfigMap keys for non-sensitive config
- Vault CSI driver paths (references, not values)

The external secret objects themselves are provisioned by the Terraform `platform` root using the ESO (External Secrets Operator) or Vault CSI provider — not by Helm chart templates.

## Environment Overlay Conventions

| Environment | Tag format | Replica min | Log level |
|-------------|-----------|-------------|-----------|
| dev | semver or `dev` | 1 | DEBUG |
| staging | semver | 2 | INFO |
| prod-eu | `sha256:<digest>` | 3 | WARNING |

## Versioning

Chart `version` tracks the chart schema version (break on template incompatibility).
`appVersion` tracks the application version (used as image tag default).

Both are bumped independently. Prefer bumping `appVersion` for routine releases and `version` only when chart templates have breaking changes.
