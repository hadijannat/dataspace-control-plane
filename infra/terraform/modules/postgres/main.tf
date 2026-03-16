# postgres module
# In production, replace this with a managed Postgres resource:
#   - Google Cloud SQL:    google_sql_database_instance
#   - AWS RDS:             aws_db_instance
#   - Azure Flexible:      azurerm_postgresql_flexible_server
#   - Crunchy Postgres:    Use the postgres-operator CRD
#
# This implementation deploys a single-node Postgres in Kubernetes — suitable for
# dev/CI environments. Not intended for production data durability.
#
# IMPORTANT: The kubernetes_secret resource below uses var.username as the password
# key name. In production, inject credentials via Vault or external-secrets-operator.
# Never store passwords in Terraform state for production workloads.

locals {
  scaffold_enabled = var.mode == "dev-scaffold"

  common_labels = merge(
    {
      "app.kubernetes.io/name"       = "postgres"
      "app.kubernetes.io/instance"   = var.instance_name
      "app.kubernetes.io/managed-by" = "terraform"
      "app.kubernetes.io/component"  = "database"
    },
    var.labels
  )
}

resource "kubernetes_persistent_volume_claim" "postgres_data" {
  count = local.scaffold_enabled ? 1 : 0

  metadata {
    name      = "${var.instance_name}-postgres-data"
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

# NOTE: In production, credentials must come from Vault, ESO, or sealed-secrets.
# This secret is a placeholder for dev environments. Sensitive values are NOT
# committed here — they must be injected via environment variables or CI secrets.
resource "kubernetes_secret" "postgres_credentials" {
  count = local.scaffold_enabled ? 1 : 0

  metadata {
    name      = "${var.instance_name}-postgres-credentials"
    namespace = var.namespace
    labels    = local.common_labels
    annotations = {
      "infra.dataspace.io/secret-type" = "postgres-credentials"
      "infra.dataspace.io/rotate"      = "manual"
    }
  }

  type = "Opaque"

  # PLACEHOLDER: replace with Vault-injected or ESO-synced values in production.
  # Never commit actual passwords here.
  data = {
    username    = base64encode(var.username)
    password    = base64encode("REPLACE_WITH_PASSWORD")
    database    = base64encode(var.database_name)
    DATABASE_URL = base64encode("postgresql://${var.username}:REPLACE_WITH_PASSWORD@${var.instance_name}-postgres:5432/${var.database_name}")
  }

  lifecycle {
    # Prevent Terraform from overwriting credentials after initial creation
    ignore_changes = [data]
  }
}

resource "kubernetes_deployment" "postgres" {
  count = local.scaffold_enabled ? 1 : 0

  metadata {
    name      = "${var.instance_name}-postgres"
    namespace = var.namespace
    labels    = local.common_labels
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/name"     = "postgres"
        "app.kubernetes.io/instance" = var.instance_name
      }
    }

    template {
      metadata {
        labels = local.common_labels
      }

      spec {
        security_context {
          run_as_non_root = true
          run_as_user     = 999
          fs_group        = 999
        }

        container {
          name  = "postgres"
          image = "postgres:${var.version}-alpine"

          port {
            container_port = 5432
            name           = "postgres"
          }

          env {
            name  = "POSTGRES_DB"
            value = var.database_name
          }

          env {
            name  = "POSTGRES_USER"
            value = var.username
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.postgres_credentials[0].metadata[0].name
                key  = "password"
              }
            }
          }

          env {
            name  = "PGDATA"
            value = "/var/lib/postgresql/data/pgdata"
          }

          volume_mount {
            name       = "postgres-data"
            mount_path = "/var/lib/postgresql/data"
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

          liveness_probe {
            exec {
              command = ["pg_isready", "-U", var.username]
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            failure_threshold     = 5
          }

          readiness_probe {
            exec {
              command = ["pg_isready", "-U", var.username]
            }
            initial_delay_seconds = 5
            period_seconds        = 5
            failure_threshold     = 3
          }
        }

        volume {
          name = "postgres-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.postgres_data[0].metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "postgres" {
  count = local.scaffold_enabled ? 1 : 0

  metadata {
    name      = "${var.instance_name}-postgres"
    namespace = var.namespace
    labels    = local.common_labels
  }

  spec {
    type = "ClusterIP"

    selector = {
      "app.kubernetes.io/name"     = "postgres"
      "app.kubernetes.io/instance" = var.instance_name
    }

    port {
      port        = 5432
      target_port = 5432
      protocol    = "TCP"
      name        = "postgres"
    }
  }
}
