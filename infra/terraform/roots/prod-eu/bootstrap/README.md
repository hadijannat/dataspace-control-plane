# prod-eu/bootstrap

Bootstrap root for production EU. Run first. Creates namespace and registry prerequisites.

**Production access requires OIDC-based authentication. Never use developer credentials.**

```bash
cd infra/terraform/roots/prod-eu/bootstrap
terraform init -backend-config=../../../backends/prod-eu.backend.hcl
terraform plan
# Require human approval before apply
terraform apply
```
