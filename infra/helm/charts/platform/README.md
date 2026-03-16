# Platform Umbrella Chart

This chart composes the internal workload charts in `infra/helm/charts/` and keeps shared release defaults in one place.

## Responsibilities

- enable or disable each workload release
- provide global defaults such as image pull policy and OTLP endpoint
- pin immutable production digests at the environment overlay level

## Usage

```bash
helm lint infra/helm/charts/platform

helm template platform infra/helm/charts/platform \
  -f infra/helm/values/dev/platform.yaml
```

Each environment overlay under `infra/helm/values/<env>/platform.yaml` should:

- set `enabled` for each subchart explicitly
- use `image.tag` for dev and staging
- use `image.digest` for production

The subcharts own their Kubernetes templates and secret references. The umbrella chart only wires release-time values.
