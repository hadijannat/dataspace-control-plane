# dev/bootstrap

Bootstrap root for the dev environment. Run this first — before platform/ or observability/.

Creates:
- `dataspace` namespace
- `terraform-state` namespace (for Kubernetes backend state storage)
- Dev container registry config

## Usage

```bash
cd infra/terraform/roots/dev/bootstrap

# Initialize (run once, or after changing required_providers)
terraform init -backend-config=../../../backends/dev.backend.hcl

# Plan
terraform plan -var-file=terraform.tfvars

# Apply
terraform apply -var-file=terraform.tfvars
```
