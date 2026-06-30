################################################################################
# Stg - Network
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
# Security Group - Bastion
################################################################################
module "bastion_sg" {
  source = "../../../modules/security-group"

  name        = "${var.environment}-${var.project_name}-bastion-sg"
  description = "Security group for bastion host - SSH from internal only"
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
