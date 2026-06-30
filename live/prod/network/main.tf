################################################################################
# Prod - Network
################################################################################
locals {
  common_tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
    Project     = var.project_name
    Owner       = var.owner
  }
}

################################################################################
# VPC
################################################################################
module "vpc" {
  source = "../../../modules/vpc"

  vpc_cidr             = var.vpc_cidr
  environment          = var.environment
  cluster_name         = "${var.project_name}-eks"
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  tags                 = local.common_tags
}

################################################################################
# Security Group - Bastion (Prod: 특정 관리 IP만 허용)
################################################################################
module "bastion_sg" {
  source = "../../../modules/security-group"

  name        = "${var.environment}-${var.project_name}-bastion-sg"
  description = "Security group for bastion host - restricted access"
  vpc_id      = module.vpc.vpc_id
  environment = var.environment

  ingress_rules = [
    {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.vpc_cidr]
      description = "SSH access from internal network only"
    }
  ]

  egress_rules = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
      description = "Allow all outbound traffic"
    }
  ]

  tags = local.common_tags
}

################################################################################
# Security Group - ALB (Prod: HTTPS only)
################################################################################
module "alb_sg" {
  source = "../../../modules/security-group"

  name        = "${var.environment}-${var.project_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = module.vpc.vpc_id
  environment = var.environment

  ingress_rules = [
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTPS from internet (fronted by WAF)"
    }
  ]

  egress_rules = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = [var.vpc_cidr]
      description = "Outbound to internal network only"
    }
  ]

  tags = local.common_tags
}
