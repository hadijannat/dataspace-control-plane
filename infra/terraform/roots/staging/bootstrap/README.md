# staging/bootstrap

Bootstrap root for the staging environment. Run first. Creates namespace and registry prerequisites.

```bash
cd infra/terraform/roots/staging/bootstrap
terraform init -backend-config=../../../backends/staging.backend.hcl
terraform apply
```
