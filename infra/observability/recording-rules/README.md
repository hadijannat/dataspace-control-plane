# Recording Rules

Recording rules pre-compute expensive queries as new time series. They reduce query latency for dashboards and alerts that use high-cardinality aggregations.

## Naming Convention

File: `<scope>-recording.yaml`

Series name: `<labels>:<metric>:<aggregation>`

Following the Prometheus recording rule naming convention:
- `<labels>` — the set of label dimensions retained (e.g. `job`, `namespace`)
- `<metric>` — the input metric base name
- `<aggregation>` — the aggregation function (e.g. `sum`, `histogram_quantile`, `rate`)

Examples:
- `job:http_server_request_rate5m:sum`
- `job:http_server_p99_latency5m:histogram_quantile`

## Loading

```yaml
# prometheus.yml
rule_files:
  - /etc/prometheus/recording-rules/*.yaml
```

Mount this directory as a ConfigMap volume or use PrometheusRule CRD (kube-prometheus-stack).

## Evaluation Interval

All recording rules in this repo use `interval: 1m`. Align with the Prometheus global `evaluation_interval`.
