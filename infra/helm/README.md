# Helm Chart Library — Dataspace Control Plane

## Purpose

`infra/helm/` owns Kubernetes release packaging only. Charts in this directory turn immutable image references plus non-secret configuration into Deployments, Services, HPAs, Ingresses, and related runtime manifests.

Helm does not provision shared infrastructure and it does not carry secret material. Secrets are always referenced by name.

## Charts

| Chart | Responsibility |
|-------|----------------|
| `platform` | Umbrella chart that composes all internal workloads for environment releases |
| `control-api` | Control-plane API service |
| `temporal-workers` | Temporal worker fleet |
| `web-console` | Web UI |
| `provisioning-agent` | Provisioning and connector automation worker |

## Image Contract

Every internal chart now uses the same image shape:

```yaml
image:
  repository: ghcr.io/your-org/dataspace-control-plane/control-api
  tag: "0.1.0"      # dev and staging
  # or
  digest: "sha256:..."  # prod-eu
```

Rules:
- `image.repository` is always required
- exactly one of `image.tag` or `image.digest` must be set
- dev and staging overlays use `image.tag`
- prod overlays use `image.digest`
- templates render `repository@digest` for digests and `repository:tag` otherwise

This is enforced in each chart `values.schema.json` and by `infra/helm/scripts/lint.sh`.

## Directory Layout

```text
infra/helm/
├── charts/
│   ├── platform/
│   ├── control-api/
│   ├── temporal-workers/
│   ├── web-console/
│   └── provisioning-agent/
├── values/
│   ├── dev/
│   ├── staging/
│   └── prod-eu/
├── scripts/
│   ├── lint.sh
│   └── render.sh
└── rendered/                  # gitignored render output
```

## Commands

Lint and render every chart/environment combination:

```bash
./infra/helm/scripts/lint.sh
```

Render a single chart with one environment overlay:

```bash
./infra/helm/scripts/render.sh --chart control-api --env dev
./infra/helm/scripts/render.sh --chart platform --env prod-eu
```

Render directly with Helm:

```bash
helm template control-api infra/helm/charts/control-api \
  -f infra/helm/values/dev/control-api.yaml

helm template platform infra/helm/charts/platform \
  -f infra/helm/values/prod-eu/platform.yaml
```

## CI Gates

`infra/helm/scripts/lint.sh` enforces the expected contract:

1. `helm lint` for every chart
2. `helm template` for every chart and every committed environment overlay
3. umbrella `platform` renders for each environment
4. schema validation through each `values.schema.json`
5. prod overlay validation: mutable tags are rejected and `image.digest` is required

The script fails clearly if `helm` or `python3` is unavailable.

## Secrets Policy

Never commit secrets, tokens, passwords, or key material into chart defaults or environment overlays.

Allowed values content:
- Kubernetes Secret names
- ExternalSecret or CSI/Vault reference names
- non-sensitive config values
- ingress hosts, ports, autoscaling, and other release metadata

Secret objects themselves are created outside Helm by the platform infrastructure path.

## Environment Conventions

| Environment | Image field | Replica baseline | Log level |
|-------------|-------------|------------------|-----------|
| `dev` | `image.tag` | 1 | DEBUG |
| `staging` | `image.tag` | 2 | INFO |
| `prod-eu` | `image.digest` | 3 | WARNING |

## Versioning

`version` tracks chart packaging compatibility. `appVersion` tracks the default application version used by development overlays.

Bump `version` only for breaking chart contract changes. Routine application releases should usually move `appVersion` or environment overlays instead.
