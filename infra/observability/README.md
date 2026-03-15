# Observability — Telemetry Stack

## Stack Overview

| Component | Role |
|-----------|------|
| OpenTelemetry Collector | Centralized OTLP receiver, processor, exporter |
| Prometheus | Metrics storage and alerting |
| Grafana | Dashboards and visualization |
| Loki | Log aggregation (staging/prod) |
| Tempo | Distributed trace storage (prod-eu) |

## Pipeline

```
apps (SDK)
  │
  │  OTLP gRPC/HTTP (port 4317/4318)
  ▼
OTel Collector
  │  processors: batch, memory_limiter, k8sattributes, redaction
  ├─── traces ───► Tempo
  ├─── metrics ──► Prometheus (remote write)
  └─── logs ─────► Loki
```

## Directory Layout

```
infra/observability/
├── otel-collector/
│   ├── base/              # Modular component configs (vendor-neutral)
│   │   ├── receivers.yaml
│   │   ├── processors.yaml
│   │   ├── exporters.yaml
│   │   ├── extensions.yaml
│   │   └── collector.yaml  # Master pipeline config
│   ├── profiles/           # Deployment mode profiles
│   │   ├── gateway.yaml    # Kubernetes Deployment (shared ingress)
│   │   ├── node-agent.yaml # DaemonSet (host metrics)
│   │   └── debug.yaml      # Local troubleshooting ONLY
│   ├── env/                # Environment endpoint overlays
│   │   ├── dev.yaml        # Local dev (no TLS, no auth)
│   │   ├── staging.yaml    # TLS + env-var auth tokens
│   │   └── prod-eu.yaml    # Strict TLS, Vault-injected tokens
│   ├── helm/               # Helm values for official OTel Collector chart
│   │   ├── values.dev.yaml
│   │   ├── values.staging.yaml
│   │   └── values.prod-eu.yaml
│   └── docker/             # Standalone configs for Docker Compose
│       ├── collector.dev.yaml   # Full dev stack
│       └── collector.test.yaml  # Minimal CI test
├── dashboards/
│   ├── README.md
│   ├── prometheus.yml          # Prometheus scrape config
│   └── control-api-overview.json  # Grafana dashboard
├── alerts/
│   ├── README.md
│   ├── control-api-alerts.yaml
│   └── temporal-workers-alerts.yaml
└── recording-rules/
    ├── README.md
    └── control-api-recording.yaml
```

## Collector Profiles

| Profile | Deployment mode | Use case |
|---------|----------------|----------|
| `gateway` | Kubernetes Deployment (2+ replicas) | Shared OTLP ingress from all pods |
| `node-agent` | Kubernetes DaemonSet | Host-level metrics |
| `debug` | Local only | Troubleshooting (NEVER production) |

## Security

- Config files contain endpoint references — auth tokens are sourced from environment variables
- **Never commit auth tokens or signing credentials** in any config file
- In Kubernetes, tokens are injected by Vault Agent Injector or External Secrets Operator
- The `redaction` processor blocks password/token/secret/private-key patterns before export
- `pprof` and `zpages` extensions are enabled in the debug profile only — never in staging/prod

## Environment Config

Auth token environment variables per environment:

| Variable | Dev | Staging/Prod |
|----------|-----|-------------|
| `TEMPO_ENDPOINT` | `http://tempo:4317` | Cloud Tempo URL |
| `TEMPO_TOKEN` | (empty) | Vault-injected |
| `PROMETHEUS_REMOTE_WRITE_URL` | `http://prometheus:9090/api/v1/write` | Cloud Prometheus URL |
| `PROMETHEUS_TOKEN` | (empty) | Vault-injected |
| `LOKI_ENDPOINT` | `http://loki:3100/loki/api/v1/push` | Cloud Loki URL |
| `LOKI_TOKEN` | (empty) | Vault-injected |
