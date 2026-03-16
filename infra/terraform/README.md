# Terraform — Dataspace Control Plane Infrastructure

## Purpose

`infra/terraform/` owns durable and shared infrastructure contracts: namespaces, registries, databases, identity, secret stores, ingress, object storage, DNS, and observability backends.

Terraform does not release application workloads. Helm owns workload packaging and Docker owns image builds.

## Structure

| Path | Responsibility |
|------|----------------|
| `modules/` | Reusable building blocks with no provider blocks |
| `roots/` | Deployable root modules grouped by environment and lifecycle |
| `backends/` | Backend config examples for non-bootstrap roots |
| `policy/` | Policy checks for plan-time enforcement |

## Module Modes

Provider-neutral shared-service modules use an explicit ownership mode:

- `dev-scaffold`: create an in-cluster development scaffold when that makes sense
- `external`: model a durable shared dependency by reference only

Current behavior:

| Module | `dev-scaffold` | `external` |
|--------|----------------|------------|
| `registry` | Records a local registry contract in-cluster | References a shared registry URL |
| `postgres` | Deploys single-node Postgres in Kubernetes | References an external Postgres host and secret |
| `keycloak` | Deploys in-cluster Keycloak | References shared Keycloak endpoints |
| `vault` | Deploys development Vault in-cluster | References shared Vault endpoints |
| `object-storage` | not used | References shared bucket or object-store URL |
| `dns` | not used | References shared DNS zone state |

Modules such as `kubernetes-namespace`, `ingress`, and `observability` remain concrete implementations because they are cluster-adjacent infrastructure managed by this repo.

## Root Layout

```text
infra/terraform/roots/
├── dev/
│   ├── bootstrap/
│   ├── platform/
│   └── observability/
├── staging/
│   ├── bootstrap/
│   ├── platform/
│   └── observability/
└── prod-eu/
    ├── bootstrap/
    ├── platform/
    └── observability/
```

Lifecycle order:

1. `bootstrap`: namespace and registry prerequisites
2. `platform`: shared runtime dependencies such as ingress, Postgres, Keycloak, and Vault
3. `observability`: Prometheus, Grafana, Loki, Tempo

## Backend Rules

Bootstrap roots use a local backend intentionally. They create the `terraform-state` namespace used by the Kubernetes backends in the later roots, so they must not depend on that namespace already existing.

Platform and observability roots continue to use the per-environment backend examples under `infra/terraform/backends/`.

Examples:

```bash
# bootstrap root
cd infra/terraform/roots/staging/bootstrap
terraform init

# platform root
cd infra/terraform/roots/staging/platform
terraform init -backend-config=../../../backends/staging.backend.hcl
```

## Secrets And State

- Never commit real `terraform.tfvars`, backend credentials, plans, or state files.
- Do not place secrets inline in `.tf` files.
- External shared services should be represented by endpoint and secret references, not secret bodies.
- Review `.terraform.lock.hcl` changes explicitly in PRs.

## Verification

For each changed root:

1. `terraform fmt -check -recursive infra/terraform`
2. `terraform validate`
3. `terraform plan` for the changed root with the correct backend and credentials
4. policy checks from `infra/terraform/policy/` where used by CI

## Provider Follow-Up

This repo now states its boundary honestly: staging and production roots reference shared durable services until a concrete provider-specific implementation is chosen. Replacing those references with real cloud resources is a follow-up decision, not an implicit behavior hidden in placeholder resources.
