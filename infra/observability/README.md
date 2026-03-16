# Observability — Telemetry Stack

## Purpose

`infra/observability/` owns telemetry topology and telemetry assets:

- OpenTelemetry Collector pipelines
- dashboards
- alerts
- recording rules

It is the telemetry control plane for both local Docker stacks and Kubernetes deployments.

## Collector Source Of Truth

Collector configuration is composed from three layers:

1. `base/`: shared receivers, processors, exporters, extensions, and common service settings
2. `profiles/`: deployment-mode wiring such as `gateway`, `node-agent`, or `debug`
3. `env/`: environment-specific endpoints, headers, TLS, and auth references

Generated outputs are committed so Docker and Helm can consume a stable artifact, but they should be regenerated from the layered source files rather than edited directly.

## Directory Layout

```text
infra/observability/
├── otel-collector/
│   ├── base/
│   ├── profiles/
│   ├── env/
│   ├── helm/
│   │   ├── source/            # human-authored Helm wrapper values
│   │   ├── values.dev.yaml    # generated
│   │   ├── values.staging.yaml
│   │   └── values.prod-eu.yaml
│   ├── docker/
│   │   ├── collector.dev.yaml # generated
│   │   └── collector.test.yaml
│   └── scripts/
│       └── render.py
├── dashboards/
├── alerts/
└── recording-rules/
```

## Profiles

| Profile | Use case | Notes |
|---------|----------|-------|
| `gateway` | Shared OTLP ingress for Kubernetes workloads | Used to generate Helm collector values |
| `node-agent` | Host or pod-local collection | Reserved for daemon-style deployments |
| `debug` | Local troubleshooting only | Keeps `pprof`, `zpages`, and debug exporters out of staging and prod |

## Rendering

Regenerate committed collector outputs after changing `base/`, `profiles/`, `env/`, or `helm/source/`:

```bash
python3 infra/observability/otel-collector/scripts/render.py
```

Current generated targets:

- `infra/observability/otel-collector/docker/collector.dev.yaml`
- `infra/observability/otel-collector/helm/values.dev.yaml`
- `infra/observability/otel-collector/helm/values.staging.yaml`
- `infra/observability/otel-collector/helm/values.prod-eu.yaml`

`collector.test.yaml` remains a hand-maintained minimal config for CI smoke paths.

## Telemetry Flow

```text
apps -> OTLP -> Collector -> Tempo / Prometheus remote write / Loki
```

Shared processors such as `memory_limiter`, `batch`, `k8sattributes`, and `redaction` live in `base/`. Profile files decide which pipelines are active.

## Security

- Never commit tokens, private keys, or secret material into collector config.
- Environment overlays should contain endpoint references and environment-variable placeholders only.
- Debug-only extensions and exporters must stay out of staging and prod outputs.
- The redaction processor remains part of the default pipeline to avoid exporting obvious secret material.

## Related Assets

Dashboards, alert rules, and recording rules are versioned alongside the Collector config because they are part of the same observability contract, even when the backend vendor differs by environment.
