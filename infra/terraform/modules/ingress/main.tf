# ingress module
# Deploys NGINX ingress controller via the official ingress-nginx Helm chart.
# Uses the helm_release resource — requires helm provider in the calling root.

resource "helm_release" "ingress_nginx" {
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = "4.10.1"
  namespace        = var.namespace
  create_namespace = true

  atomic          = true
  cleanup_on_fail = true
  timeout         = 300

  set {
    name  = "controller.replicaCount"
    value = var.replicas
  }

  set {
    name  = "controller.service.type"
    value = "LoadBalancer"
  }

  set {
    name  = "controller.ingressClassResource.name"
    value = var.class_name
  }

  set {
    name  = "controller.ingressClassResource.default"
    value = "false"
  }

  # Security: enable HSTS and SSL redirect by default
  set {
    name  = "controller.config.ssl-redirect"
    value = "false"  # Managed at Ingress resource level
  }

  set {
    name  = "controller.config.use-forwarded-headers"
    value = "true"
  }

  set {
    name  = "controller.metrics.enabled"
    value = "true"
  }

  set {
    name  = "controller.metrics.serviceMonitor.enabled"
    value = "false"  # Enable when Prometheus Operator is deployed
  }

  # Resource requests/limits for the controller
  set {
    name  = "controller.resources.requests.cpu"
    value = "100m"
  }

  set {
    name  = "controller.resources.requests.memory"
    value = "128Mi"
  }

  set {
    name  = "controller.resources.limits.cpu"
    value = "500m"
  }

  set {
    name  = "controller.resources.limits.memory"
    value = "512Mi"
  }
}
