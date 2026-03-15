package terraform.policy

# Deny Kubernetes resources that do not have the app.kubernetes.io/managed-by label.
# All K8s resources created by Terraform must declare managed-by=terraform so that
# ownership is traceable and orphan detection works correctly.

kubernetes_resource_types := {
  "kubernetes_namespace",
  "kubernetes_deployment",
  "kubernetes_service",
  "kubernetes_config_map",
  "kubernetes_secret",
  "kubernetes_persistent_volume_claim",
  "kubernetes_service_account",
  "kubernetes_ingress_v1",
  "kubernetes_horizontal_pod_autoscaler_v2",
}

deny[msg] {
  resource := input.resource_changes[_]
  kubernetes_resource_types[resource.type]
  resource.change.action != "delete"

  labels := resource.change.after.metadata[0].labels

  not labels["app.kubernetes.io/managed-by"]

  msg := sprintf(
    "Kubernetes resource '%v' of type '%v' is missing the required label 'app.kubernetes.io/managed-by'. All Terraform-managed K8s resources must include this label.",
    [resource.address, resource.type]
  )
}

deny[msg] {
  resource := input.resource_changes[_]
  kubernetes_resource_types[resource.type]
  resource.change.action != "delete"

  labels := resource.change.after.metadata[0].labels
  labels["app.kubernetes.io/managed-by"] != "terraform"

  msg := sprintf(
    "Kubernetes resource '%v' has label 'app.kubernetes.io/managed-by=%v' but expected 'terraform'. Terraform-managed resources must use 'terraform' as the managed-by value.",
    [resource.address, labels["app.kubernetes.io/managed-by"]]
  )
}
