# vault module
# Deploys HashiCorp Vault in Kubernetes (dev/staging mode).
#
# In production, use the official Vault Helm chart directly or the Vault Terraform provider
# for engine and policy configuration:
#   - Vault Helm chart: https://github.com/hashicorp/vault-helm
#   - Vault provider: registry.terraform.io/hashicorp/vault
#
# For HA (ha_enabled=true), this module enables Raft integrated storage.
# In production, configure unseal keys via Vault Auto Unseal (AWS KMS, GCP Cloud KMS, etc.)
# rather than dev mode.
#
# CRITICAL SECURITY NOTE:
# This module runs Vault in dev mode (-dev) for local environments.
# Dev mode stores the root token in VAULT_DEV_ROOT_TOKEN_ID env var.
# NEVER run dev mode in production. See root module README for production setup.

locals {
  common_labels = merge(
    {
      "app.kubernetes.io/name"       = "vault"
      "app.kubernetes.io/managed-by" = "terraform"
      "app.kubernetes.io/component"  = "secrets-manager"
    },
    var.labels
  )

  replicas = var.ha_enabled ? 3 : 1
}

resource "kubernetes_persistent_volume_claim" "vault_data" {
  metadata {
    name      = "vault-data"
    namespace = var.namespace
    labels    = local.common_labels
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = var.storage_size
      }
    }
  }
}

resource "kubernetes_deployment" "vault" {
  metadata {
    name      = "vault"
    namespace = var.namespace
    labels    = local.common_labels
  }

  spec {
    replicas = local.replicas

    selector {
      match_labels = {
        "app.kubernetes.io/name" = "vault"
      }
    }

    template {
      metadata {
        labels = local.common_labels
      }

      spec {
        security_context {
          run_as_non_root = false  # Vault requires root for IPC_LOCK capability in production
        }

        container {
          name  = "vault"
          image = "hashicorp/vault:1.17"

          # In production, replace with 'vault server' command and a proper config file.
          # Dev mode is for local development ONLY.
          args = ["server", "-dev"]

          port {
            container_port = 8200
            name           = "api"
          }

          port {
            container_port = 8201
            name           = "cluster"
          }

          env {
            name  = "VAULT_DEV_LISTEN_ADDRESS"
            value = "0.0.0.0:8200"
          }

          env {
            name = "VAULT_DEV_ROOT_TOKEN_ID"
            value_from {
              secret_key_ref {
                name = "vault-dev-token"
                key  = "root-token"
                optional = true
              }
            }
          }

          env {
            name  = "VAULT_ADDR"
            value = "http://127.0.0.1:8200"
          }

          security_context {
            capabilities {
              add = ["IPC_LOCK"]
            }
          }

          volume_mount {
            name       = "vault-data"
            mount_path = "/vault/data"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }

          readiness_probe {
            http_get {
              path = "/v1/sys/health?standbyok=true&uninitcode=204&sealedcode=204"
              port = 8200
            }
            initial_delay_seconds = 10
            period_seconds        = 10
            failure_threshold     = 3
          }

          liveness_probe {
            http_get {
              path = "/v1/sys/health?standbyok=true&uninitcode=204&sealedcode=204"
              port = 8200
            }
            initial_delay_seconds = 30
            period_seconds        = 30
            failure_threshold     = 5
          }
        }

        volume {
          name = "vault-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.vault_data.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "vault" {
  metadata {
    name      = "vault"
    namespace = var.namespace
    labels    = local.common_labels
  }

  spec {
    type = "ClusterIP"

    selector = {
      "app.kubernetes.io/name" = "vault"
    }

    port {
      port        = 8200
      target_port = 8200
      protocol    = "TCP"
      name        = "api"
    }

    port {
      port        = 8201
      target_port = 8201
      protocol    = "TCP"
      name        = "cluster"
    }
  }
}

# NOTE: In production, use the vault Terraform provider to enable secrets engines:
#   provider "vault" { address = "https://vault.example.com" }
#   resource "vault_mount" "transit" { path = "transit"; type = "transit" }
#   resource "vault_mount" "pki"     { path = "pki";     type = "pki"     }
#
# The null_resource below runs vault CLI commands as a post-deploy step for dev.
# This requires the vault CLI to be available in the Terraform execution environment.

resource "null_resource" "vault_engine_init" {
  count = (var.transit_enabled || var.pki_enabled) ? 1 : 0

  depends_on = [kubernetes_deployment.vault]

  # IMPORTANT: This triggers on Vault deployment changes only.
  # Do NOT re-run engine initialization on every plan (it is idempotent but noisy).
  triggers = {
    vault_deployment_generation = kubernetes_deployment.vault.metadata[0].resource_version
  }

  provisioner "local-exec" {
    # This script enables Transit and PKI engines in Vault after startup.
    # It will retry until Vault is ready (up to 60s).
    # Requires: vault CLI, VAULT_ADDR, VAULT_TOKEN environment variables.
    command = <<-EOT
      set -e
      echo "Waiting for Vault to be ready..."
      for i in $(seq 1 12); do
        vault status > /dev/null 2>&1 && break
        sleep 5
      done

      ${var.transit_enabled ? "vault secrets enable transit 2>/dev/null || echo 'Transit already enabled'" : "echo 'Transit engine disabled'"}
      ${var.pki_enabled ? "vault secrets enable pki 2>/dev/null || echo 'PKI already enabled'" : "echo 'PKI engine disabled'"}
      ${var.pki_enabled ? "vault secrets tune -max-lease-ttl=87600h pki" : ""}

      echo "Vault engine initialization complete."
    EOT

    environment = {
      VAULT_ADDR = "http://vault.${var.namespace}.svc.cluster.local:8200"
      # VAULT_TOKEN must be set in the calling environment — never hardcoded here.
    }
  }
}
