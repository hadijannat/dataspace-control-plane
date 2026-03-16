# staging/platform

Connects staging to shared Postgres, Keycloak, and Vault services through external references, and deploys the shared ingress controller in-cluster.

Expected `terraform.tfvars` values include the shared service hostnames, URLs, and secret names consumed by downstream workloads.

```bash
cd infra/terraform/roots/staging/platform
terraform init -backend-config=../../../backends/staging.backend.hcl
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```
