# keycloak module
# In production, use the Keycloak Terraform provider or a managed identity service:
#   - Keycloak provider: registry.terraform.io/mrparkers/keycloak
#   - Auth0:             registry.terraform.io/auth0/auth0
#   - Azure AD B2C:      azurerm_aadb2c_directory
#
# This implementation creates a Kubernetes Deployment + Service + PVC for Keycloak.
# Suitable for dev/staging. For production: use HA Keycloak with external DB or a
# managed identity platform.

locals {
  common_labels = merge(
    {
      "app.kubernetes.io/name"       = "keycloak"
      "app.kubernetes.io/instance"   = var.realm_name
      "app.kubernetes.io/managed-by" = "terraform"
      "app.kubernetes.io/component"  = "identity"
    },
    var.labels
  )
}

resource "kubernetes_persistent_volume_claim" "keycloak_data" {
  metadata {
    name      = "keycloak-data"
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

resource "kubernetes_deployment" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = var.namespace
    labels    = local.common_labels
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/name" = "keycloak"
      }
    }

    template {
      metadata {
        labels = local.common_labels
      }

      spec {
        security_context {
          run_as_non_root = true
          run_as_user     = 1000
          fs_group        = 1000
        }

        container {
          name  = "keycloak"
          image = "quay.io/keycloak/keycloak:24.0"
          args  = ["start-dev"]

          port {
            container_port = 8080
            name           = "http"
          }

          env {
            name  = "KEYCLOAK_ADMIN"
            value = "admin"
          }

          env {
            name = "KEYCLOAK_ADMIN_PASSWORD"
            value_from {
              secret_key_ref {
                name = var.admin_secret_name
                key  = "ADMIN_PASSWORD"
              }
            }
          }

          env {
            name  = "KC_HOSTNAME_STRICT"
            value = "false"
          }

          env {
            name  = "KC_HTTP_ENABLED"
            value = "true"
          }

          volume_mount {
            name       = "keycloak-data"
            mount_path = "/opt/keycloak/data"
          }

          resources {
            requests = {
              cpu    = "200m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "1000m"
              memory = "1Gi"
            }
          }

          readiness_probe {
            http_get {
              path = "/health/ready"
              port = 8080
            }
            initial_delay_seconds = 60
            period_seconds        = 10
            failure_threshold     = 10
          }

          liveness_probe {
            http_get {
              path = "/health/live"
              port = 8080
            }
            initial_delay_seconds = 90
            period_seconds        = 30
            failure_threshold     = 5
          }
        }

        volume {
          name = "keycloak-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.keycloak_data.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = var.namespace
    labels    = local.common_labels
  }

  spec {
    type = "ClusterIP"

    selector = {
      "app.kubernetes.io/name" = "keycloak"
    }

    port {
      port        = 8080
      target_port = 8080
      protocol    = "TCP"
      name        = "http"
    }
  }
}
