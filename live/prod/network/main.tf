################################################################################
# Prod - Network
################################################################################
locals {
  environment  = "prod"
  project_name = "myproject"
  owner        = "platform-team"
  aws_region   = "ap-northeast-2"

  common_tags = {
    Environment = local.environment
    ManagedBy   = "terraform"
    Project     = local.project_name
    Owner       = local.owner
  }
}

################################################################################
# VPC
################################################################################
module "vpc" {
  source = "../../../modules/vpc"

  vpc_cidr             = "10.30.0.0/16"
  environment          = local.environment
  cluster_name         = "${local.project_name}-eks"
  public_subnet_cidrs  = ["10.30.1.0/24", "10.30.2.0/24", "10.30.3.0/24"]
  private_subnet_cidrs = ["10.30.11.0/24", "10.30.12.0/24", "10.30.13.0/24"]
  tags                 = local.common_tags
}

################################################################################
# Security Group - Bastion (Prod: 특정 관리 IP만 허용)
################################################################################
module "bastion_sg" {
  source = "../../../modules/security-group"

  name        = "${local.environment}-${local.project_name}-bastion-sg"
  description = "Security group for bastion host - restricted access"
  vpc_id      = module.vpc.vpc_id
  environment = local.environment

  ingress_rules = [
    {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["10.30.0.0/16"]
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

  name        = "${local.environment}-${local.project_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = module.vpc.vpc_id
  environment = local.environment

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
      cidr_blocks = ["10.30.0.0/16"]
      description = "Outbound to internal network only"
    }
  ]

  tags = local.common_tags
}
