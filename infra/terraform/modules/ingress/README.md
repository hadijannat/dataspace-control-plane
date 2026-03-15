# Module: ingress

Deploys the NGINX ingress controller via the official `ingress-nginx` Helm chart (version 4.10.1).

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `namespace` | string | — | yes | Target namespace |
| `class_name` | string | `"nginx"` | no | IngressClass name |
| `replicas` | number | `2` | no | Controller replicas (1–10) |
| `labels` | map(string) | `{}` | no | Resource labels |

## Outputs

| Name | Description |
|------|-------------|
| `controller_service_name` | LoadBalancer service name |
| `class_name` | IngressClass name |
