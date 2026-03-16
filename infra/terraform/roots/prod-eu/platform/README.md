# prod-eu/platform

Connects production EU to shared Postgres, Keycloak, Vault, and object storage services through external references, and deploys ingress in-cluster.

This root should be applied from a reviewed plan. It does not create provider-specific durable services yet; it models their contract explicitly.

```bash
cd infra/terraform/roots/prod-eu/platform
terraform init -backend-config=../../../backends/prod-eu.backend.hcl
terraform plan -out=prod-eu-platform.tfplan -var-file=terraform.tfvars
terraform apply prod-eu-platform.tfplan
```
