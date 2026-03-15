# Grafana Dashboards

Dashboard JSON files live in this directory. They are auto-provisioned by Grafana via a dashboard provisioner ConfigMap (see Helm values or Docker Compose volume mount).

## Naming Convention

`<service>-<signal>.json`

Examples:
- `control-api-overview.json` — request rate, latency, error rate
- `temporal-workers-overview.json` — queue depth, activity failures, workflow success rate
- `platform-infrastructure.json` — node metrics, Postgres, Vault health

## Generation

| Dashboard | Source | Status |
|-----------|--------|--------|
| `control-api-overview.json` | Hand-authored | Active |

Dashboards are maintained as exported Grafana JSON (version 1, schemaVersion 38+). To update:

1. Edit in Grafana UI (local dev stack)
2. Export: Dashboard settings → JSON Model → Copy to clipboard
3. Save to this directory and commit

## Grafana Provisioner Config

Add to Grafana Helm values to auto-load dashboards from this directory:

```yaml
grafana:
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: dataspace
          orgId: 1
          folder: Dataspace
          type: file
          disableDeletion: false
          editable: true
          options:
            path: /var/lib/grafana/dashboards
  dashboards:
    dataspace:
      control-api-overview:
        file: dashboards/control-api-overview.json
```

Or mount this directory as a ConfigMap volume at `/var/lib/grafana/dashboards`.
