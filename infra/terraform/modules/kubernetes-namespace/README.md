# Module: kubernetes-namespace

Creates a Kubernetes namespace with standard `app.kubernetes.io/managed-by: terraform` label and optional custom labels/annotations.

No provider block — auth is inherited from the calling root module.

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `name` | string | — | yes | Namespace name (DNS label format) |
| `labels` | map(string) | `{}` | no | Additional namespace labels |
| `annotations` | map(string) | `{}` | no | Namespace annotations |

## Outputs

| Name | Description |
|------|-------------|
| `name` | Namespace name |
| `uid` | Namespace UID |

## Example

```hcl
module "dataspace_namespace" {
  source = "../../modules/kubernetes-namespace"

  name = "dataspace"
  labels = {
    "app.kubernetes.io/part-of" = "dataspace-control-plane"
    "environment"               = "dev"
  }
}
```
