output "alb_controller_status" {
  description = "AWS Load Balancer Controller Helm release status"
  value       = helm_release.aws_load_balancer_controller.status
}

output "cluster_autoscaler_status" {
  description = "Cluster Autoscaler Helm release status"
  value       = helm_release.cluster_autoscaler.status
}

output "external_dns_status" {
  description = "External DNS Helm release status"
  value       = helm_release.external_dns.status
}
