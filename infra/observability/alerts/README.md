# Alert Rules

Alert rule files in this directory use Prometheus alerting rule format (YAML).

## Naming Convention

`<scope>-alerts.yaml`

Examples:
- `control-api-alerts.yaml`
- `temporal-workers-alerts.yaml`
- `infrastructure-alerts.yaml`

## Loading

These files are loaded by Prometheus via `rule_files` configuration:

```yaml
rule_files:
  - /etc/prometheus/alerts/*.yaml
```

In Kubernetes, mount this directory as a ConfigMap volume in the Prometheus pod (or use the PrometheusRule CRD with kube-prometheus-stack).

## Severity Labels

| Severity | Routing |
|----------|---------|
| `critical` | PagerDuty (24/7 on-call) |
| `warning` | Slack #platform-alerts |
| `info` | Log only — no notification |

## Runbook Convention

Each alert SHOULD include an `annotations.runbook` URL pointing to the operator runbook in `docs/runbooks/`.

## Alert Groups

Keep related alerts in the same group. One file per service or infrastructure component.
