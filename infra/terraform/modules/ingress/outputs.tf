output "controller_service_name" {
  value       = "ingress-nginx-controller"
  description = "Name of the ingress-nginx controller Service (LoadBalancer)."
}

output "class_name" {
  value       = var.class_name
  description = "IngressClass name to reference in Ingress resources."
}
