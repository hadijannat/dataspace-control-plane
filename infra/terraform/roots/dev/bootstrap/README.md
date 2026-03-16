# dev/bootstrap

Creates the `dataspace` and `terraform-state` namespaces, then records the local dev registry contract.

This root uses a local backend on purpose because it creates the namespace that later Kubernetes-backed roots rely on.

```bash
cd infra/terraform/roots/dev/bootstrap
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```
