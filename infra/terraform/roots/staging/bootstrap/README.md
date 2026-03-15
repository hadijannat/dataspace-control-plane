# staging/bootstrap

Creates the `dataspace` and `terraform-state` namespaces for staging and records the shared staging registry contract.

This root uses a local backend to avoid a circular dependency on the namespace that stores later Terraform state.

```bash
cd infra/terraform/roots/staging/bootstrap
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```
