variable "environment" {
  description = "Environment name (dev, stg, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "owner" {
  description = "Team or person responsible"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "state_bucket" {
  description = "S3 bucket for remote state reference"
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR for ALB controller"
  type        = string
}
