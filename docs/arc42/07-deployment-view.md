---
title: "7. Deployment View"
summary: "Kubernetes namespace layout, infrastructure provisioning order, and deployment topology for the dataspace control plane."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# 7. Deployment View

## Kubernetes Namespace Layout

The platform is deployed on Kubernetes, split across four namespaces with strict network policy boundaries. Cross-namespace traffic is permitted only on the interfaces documented in [Section 3 (Context and Scope)](03-context-and-scope.md).

```mermaid
graph TB
    Ingress[Nginx Ingress\nLoad Balancer\next IP]

    subgraph NS_platform["namespace: dataspace-platform"]
        CA[control-api\nDeployment\n2-4 replicas]
        TW[temporal-workers\nDeployment\n2-8 replicas]
        WC[web-console\nDeployment\n2 replicas]
        PA[provisioning-agent\nDeployment\n1 replica]
        OC[otel-collector\nDeployment\n1 replica]
    end

    subgraph NS_infra["namespace: dataspace-infra"]
        KC[Keycloak\nStatefulSet\n2 replicas HA]
        VT[Vault\nStatefulSet\n3 replicas HA]
        PG[PostgreSQL\nStatefulSet\n1 primary + 1 replica]
        KF[Kafka\nStatefulSet\n3 brokers]
    end

    subgraph NS_temporal["namespace: temporal"]
        TS[Temporal Server\nDeployment]
        TDB[Temporal PostgreSQL\nStatefulSet]
        TUI[Temporal UI\nDeployment]
    end

    subgraph NS_obs["namespace: observability"]
        PROM[Prometheus\nStatefulSet]
        GRAF[Grafana\nDeployment]
        LOKI[Loki\nStatefulSet]
        ALERT[AlertManager\nDeployment]
    end

    Ingress -->|443/HTTPS| CA
    Ingress -->|443/HTTPS| WC
    Ingress -->|443/HTTPS - internal only| TUI

    CA -->|5432/TLS| PG
    CA -->|8200/HTTPS| VT
    CA -->|8080/HTTPS| KC
    CA -->|7233/gRPC| TS

    TW -->|7233/gRPC| TS
    TW -->|8200/HTTPS| VT
    TW -->|8080/HTTPS| KC
    TW -->|5432/TLS| PG
    TW -->|9092/TLS| KF

    PA -->|DSP 8080| EDC[EDC Connector\next namespace]
    PA -->|8081/HTTPS| BaSyx[BaSyx AAS\next namespace]
    PA -->|8080/HTTPS| KC

    OC -->|4317/gRPC OTLP in| CA
    OC -->|4317/gRPC OTLP in| TW
    OC -->|9090| PROM
    OC -->|3100| LOKI

    TS -->|5432/TLS| TDB
```

## Component Resources

| Component | CPU request | CPU limit | Memory request | Memory limit | Storage |
|-----------|------------|-----------|---------------|-------------|---------|
| control-api | 250m | 1000m | 512Mi | 1Gi | — |
| temporal-workers | 500m | 2000m | 1Gi | 2Gi | — |
| web-console | 100m | 500m | 256Mi | 512Mi | — |
| provisioning-agent | 100m | 500m | 256Mi | 512Mi | — |
| PostgreSQL | 500m | 2000m | 2Gi | 4Gi | 50Gi SSD PVC |
| Vault | 250m | 1000m | 512Mi | 1Gi | 10Gi SSD PVC |
| Keycloak | 500m | 2000m | 1Gi | 2Gi | PostgreSQL (shared) |
| Temporal Server | 500m | 2000m | 1Gi | 2Gi | Temporal PostgreSQL |
| Kafka | 1000m | 4000m | 2Gi | 4Gi | 100Gi SSD PVC per broker |

## Infrastructure Provisioning Order

Infrastructure is provisioned in a strict order to ensure each layer's dependencies are available before it is installed. This order is enforced by Terraform module `depends_on` declarations and Helm post-install hooks.

```
Step 1: terraform bootstrap
  → Creates: VPC, subnets, DNS zones, TLS certificates (ACM/Vault PKI bootstrap)
  → Outputs: cluster endpoint, service account annotations

Step 2: terraform platform
  → Creates: PostgreSQL cluster, Keycloak deployment, Vault cluster + auto-unseal config, Kafka cluster, Nginx ingress
  → Outputs: connection strings, Keycloak admin credentials (stored in Vault), Vault root token (rotated immediately)

Step 3: docker bake release
  → Builds and pushes: control-api, temporal-workers, web-console, provisioning-agent images
  → Tags with git SHA; pushes to internal registry

Step 4: helm upgrade dataspace-platform
  → Installs: control-api, temporal-workers, web-console, provisioning-agent, otel-collector
  → Requires: Vault, Keycloak, PostgreSQL ready (checked via Helm pre-install hook)
  → Post-install: runs database migrations, bootstraps Temporal namespace, seeds Keycloak realm template

Step 5: terraform observability
  → Creates: Prometheus, Grafana, Loki, AlertManager
  → Configures: Grafana data sources, dashboard provisioning from infra/observability/dashboards/

Step 6: helm upgrade otel-collector
  → Configures: OTLP receiver, redaction processor (blocks token/key/password patterns), Prometheus exporter, Loki exporter
```

## Vault Initialization and Seal Management

Vault is initialized once during bootstrap. The initialization sequence:

1. `vault operator init -key-shares=5 -key-threshold=3` → generates 5 unseal key shards and the root token
2. Unseal key shards are distributed to 3 separate Vault operators via secure channel (PGP-encrypted)
3. Root token is used once to configure auth methods, then revoked
4. Auto-unseal is configured using cloud KMS (AWS KMS or GCP Cloud KMS) for HA deployments
5. Vault policies for platform service accounts are applied via Terraform `vault` provider

See [runbooks/platform/vault-key-rotation.md](../runbooks/platform/vault-key-rotation.md) for key rotation procedure.

## Ingress and TLS

All public-facing ingress is TLS-terminated at the Nginx ingress controller. Certificates are managed by cert-manager with Vault PKI as the issuer for internal services and Let's Encrypt for public endpoints.

| Host | Target service | Certificate issuer |
|------|---------------|-------------------|
| `api.your-org.internal` | control-api | Vault PKI (internal CA) |
| `console.your-org.internal` | web-console | Vault PKI (internal CA) |
| `temporal.your-org.internal` | Temporal UI | Vault PKI (internal CA, restricted to VPN) |
| `api.your-org.com` | control-api | Let's Encrypt (public) |

## Environment Tiers

| Tier | Purpose | Notes |
|------|---------|-------|
| `local` | Developer local development | `docker compose up` with mock Vault and Keycloak |
| `dev` | Integration testing of in-progress features | Full Kubernetes stack, auto-deployed from `main` branch |
| `staging` | Pre-release validation | Production-equivalent config; TCK compatibility tests run here |
| `prod` | Production | HA Vault, HA Keycloak, multi-AZ PostgreSQL, PagerDuty alerting |
