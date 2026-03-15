# dev/platform

Deploys development scaffolds for Postgres, Keycloak, and Vault, plus the shared ingress controller.

Use this root after `dev/bootstrap`. It uses the environment backend example because the state namespace already exists.

```bash
cd infra/terraform/roots/dev/platform
terraform init -backend-config=../../../backends/dev.backend.hcl
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```
