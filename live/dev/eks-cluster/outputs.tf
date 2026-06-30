output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "alb_controller_role_arn" {
  description = "ALB Controller IRSA Role ARN"
  value       = module.irsa_alb_controller.role_arn
}

output "cluster_autoscaler_role_arn" {
  description = "Cluster Autoscaler IRSA Role ARN"
  value       = module.irsa_cluster_autoscaler.role_arn
}

output "external_dns_role_arn" {
  description = "External DNS IRSA Role ARN"
  value       = module.irsa_external_dns.role_arn
}
