# dev/platform

Platform root for the dev environment. Deploys Postgres, Keycloak, Vault, and NGINX ingress.

Run after `dev/bootstrap/`.

## Usage

```bash
cd infra/terraform/roots/dev/platform
terraform init -backend-config=../../../backends/dev.backend.hcl
terraform plan
terraform apply
```
