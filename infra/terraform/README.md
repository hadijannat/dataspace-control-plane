# Terraform — Dataspace Control Plane Infrastructure

## Purpose

This directory owns durable shared infrastructure: Kubernetes namespaces, Postgres instances, Keycloak, Vault, ingress controllers, object storage, DNS, and observability backends. Terraform provisions long-lived resources that workloads (Helm-managed) depend on.

**Terraform does not deploy application workloads.** Application releases are managed by Helm. The boundary is: Terraform → infrastructure substrate; Helm → workload releases.

## Layer Ownership

| Path | Responsibility |
|------|---------------|
| `modules/` | Reusable, composable infrastructure building blocks (no provider blocks) |
| `roots/` | Deployable Terraform stacks — one root per environment + lifecycle layer |
| `backends/` | Backend config examples (never commit real credentials) |
| `policy/` | OPA/Sentinel policy files for plan-time enforcement |

## Module List

| Module | Purpose |
|--------|---------|
| `kubernetes-namespace` | Creates a K8s namespace with labels and annotations |
| `registry` | Container registry project (provider-specific — see module README) |
| `postgres` | PostgreSQL instance (provider-specific placeholder — see module README) |
| `keycloak` | Keycloak identity server (K8s deployment for dev, external for prod) |
| `vault` | HashiCorp Vault (K8s deployment, transit + PKI engine enablement) |
| `object-storage` | Object storage bucket (provider-specific placeholder) |
| `dns` | DNS zone and records (provider-specific placeholder) |
| `ingress` | NGINX ingress controller via Helm release |
| `observability` | kube-prometheus-stack and optional Loki/Tempo via Helm releases |

## Root Layout

```
roots/
├── dev/
│   ├── bootstrap/    # Namespace + registry — run first in each env
│   ├── platform/     # Postgres, Keycloak, Vault, ingress — run second
│   └── observability/ # Monitoring stack — run third
├── staging/
│   ├── bootstrap/
│   ├── platform/
│   └── observability/
└── prod-eu/
    ├── bootstrap/
    ├── platform/
    └── observability/
```

### Lifecycle Layers

1. **bootstrap** — namespace and registry prerequisites; run once, rarely changed
2. **platform** — shared services (Postgres, Keycloak, Vault, ingress); changed on platform upgrades
3. **observability** — monitoring stack; changed on alert/dashboard/SLO changes

Each layer is a separate Terraform root with independent state. This limits blast radius: changing the observability stack cannot accidentally destroy platform resources.

## How to Run Each Root

```bash
# Example: dev/platform
cd infra/terraform/roots/dev/platform

# Initialize (populates .terraform/ and .terraform.lock.hcl)
terraform init -backend-config=../../../backends/dev.backend.hcl

# Preview changes
terraform plan -var-file=terraform.tfvars

# Apply changes
terraform apply -var-file=terraform.tfvars

# Validate without connecting to provider
terraform validate
```

## Secret Rules

- **No inline secrets** in `.tf` files or committed `*.tfvars` files
- Provider authentication via environment variables:
  - AWS: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
  - GCP: `GOOGLE_APPLICATION_CREDENTIALS`
  - Azure: `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`
  - Kubernetes: `KUBECONFIG` env var or in-cluster service account
- Vault root token: never committed — retrieve from sealed Vault after bootstrap
- Commit `*.tfvars.example` with safe example values; gitignore actual `*.tfvars`

## Lock File Policy

- Commit `.terraform.lock.hcl` in every root after running `terraform init`
- Provider version changes must be reviewed in PR diff — never auto-accept lock file changes
- Run `terraform init -upgrade` only when intentionally updating provider versions
- Use `-lockfile=readonly` in CI to enforce the committed lock file

## CI Gates

For each changed root:
1. `terraform fmt -check` — enforces canonical formatting
2. `terraform validate` — syntax and type checking (no provider connection required)
3. `terraform plan -out=plan.tfplan` — full plan with provider (requires credentials)
4. Policy check: `conftest test plan.tfplan -p infra/terraform/policy/` (OPA policies)
5. Plan artifact archived for human review before apply

## Provider Selection Note

Most modules in this repo contain provider-agnostic placeholders or Kubernetes-based implementations. Before first deployment, select the appropriate provider resources based on your cloud/on-prem environment and substitute placeholders as documented in each module's README.
