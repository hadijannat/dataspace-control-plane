# prod-eu/platform

Production EU platform services. Postgres 100Gi, Vault HA, ingress 3 replicas, object storage.

**Production changes require approval. Never apply without a reviewed plan.**

```bash
cd infra/terraform/roots/prod-eu/platform
terraform init -backend-config=../../../backends/prod-eu.backend.hcl
terraform plan -out=prod-eu-platform.tfplan
# Review plan → get approval → apply
terraform apply prod-eu-platform.tfplan
```
