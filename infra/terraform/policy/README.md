# Terraform Policy Enforcement

Policy files in this directory enforce security and compliance constraints on Terraform plans at CI time.

## Policy Framework

Use one of:
- **Sentinel** (HCP Terraform / Terraform Enterprise): embed `.sentinel` files and configure in HCP Terraform workspace settings
- **OPA with conftest** (open-source): recommended for self-hosted CI

### Using conftest

```bash
# Install conftest
brew install conftest   # macOS
# or: https://www.conftest.dev/install/

# Generate plan JSON
cd infra/terraform/roots/dev/platform
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json

# Test against policies
conftest test plan.json -p infra/terraform/policy/
```

## Policy Files

| File | Description |
|------|-------------|
| `no_public_s3.rego` | Denies S3 buckets with public ACL |
| `require_labels.rego` | Denies K8s resources without `app.kubernetes.io/managed-by` label |

## Severity

All policies in this directory are **hard failures** — CI must not apply if they fail.

## Adding Policies

Name new policy files `<concern>.rego`. All `.rego` files in this directory are automatically picked up by `conftest test -p infra/terraform/policy/`.

Keep policies focused on security and compliance invariants, not architectural style. Architecture is enforced via code review.
