output "role_arn" {
  description = "IAM Role ARN (use this in ServiceAccount annotation)"
  value       = aws_iam_role.this.arn
}

output "role_name" {
  description = "IAM Role name"
  value       = aws_iam_role.this.name
}
