# observability module
# Deploys the Prometheus observability stack using kube-prometheus-stack Helm chart.
# Optional: Loki (log aggregation) and Tempo (distributed tracing).

resource "kubernetes_namespace" "observability" {
  metadata {
    name = var.namespace
    labels = merge(
      {
        "app.kubernetes.io/managed-by" = "terraform"
        "app.kubernetes.io/component"  = "observability"
      },
      var.labels
    )
  }
}

resource "helm_release" "kube_prometheus_stack" {
  name             = "kube-prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = "61.3.0"
  namespace        = var.namespace
  create_namespace = false

  depends_on = [kubernetes_namespace.observability]

  atomic          = true
  cleanup_on_fail = true
  timeout         = 600

  # Grafana
  set {
    name  = "grafana.enabled"
    value = var.grafana_enabled
  }

  set {
    name  = "grafana.adminPassword"
    value = "REPLACE_WITH_SECRET_VALUE"  # In production, inject via grafana.adminPassword from K8s secret
  }

  # Prometheus storage
  set {
    name  = "prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage"
    value = var.prometheus_storage_size
  }

  set {
    name  = "prometheus.prometheusSpec.retention"
    value = "30d"
  }

  set {
    name  = "prometheus.prometheusSpec.retentionSize"
    value = "45GiB"
  }

  # AlertManager
  set {
    name  = "alertmanager.enabled"
    value = "true"
  }

  # Disable components not needed by default (enable per-env in roots)
  set {
    name  = "kubeEtcd.enabled"
    value = "false"
  }

  set {
    name  = "kubeScheduler.enabled"
    value = "false"
  }

  set {
    name  = "kubeControllerManager.enabled"
    value = "false"
  }
}

# Optional: Loki for log aggregation
resource "helm_release" "loki" {
  count = var.loki_enabled ? 1 : 0

  name             = "loki"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "loki"
  version          = "6.6.4"
  namespace        = var.namespace
  create_namespace = false

  depends_on = [kubernetes_namespace.observability]

  atomic          = true
  cleanup_on_fail = true
  timeout         = 300

  set {
    name  = "loki.auth_enabled"
    value = "false"
  }

  set {
    name  = "loki.commonConfig.replication_factor"
    value = "1"
  }

  set {
    name  = "loki.storage.type"
    value = "filesystem"
  }

  set {
    name  = "singleBinary.replicas"
    value = "1"
  }
}

# Optional: Tempo for distributed trace storage
resource "helm_release" "tempo" {
  count = var.tempo_enabled ? 1 : 0

  name             = "tempo"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "tempo"
  version          = "1.9.0"
  namespace        = var.namespace
  create_namespace = false

  depends_on = [kubernetes_namespace.observability]

  atomic          = true
  cleanup_on_fail = true
  timeout         = 300

  set {
    name  = "tempo.storage.trace.backend"
    value = "local"
  }
}
