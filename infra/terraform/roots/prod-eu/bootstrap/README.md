# prod-eu/bootstrap

Creates the `dataspace` and `terraform-state` namespaces for the EU production environment and records the shared production registry contract.

This root uses a local backend for the same reason as the other bootstrap roots: it creates the namespace that later remote state depends on.

```bash
cd infra/terraform/roots/prod-eu/bootstrap
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```
