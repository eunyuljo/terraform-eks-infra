################################################################################
# Dev - Network
################################################################################
locals {
  environment  = "dev"
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

  vpc_cidr             = "10.10.0.0/16"
  environment          = local.environment
  cluster_name         = "${local.project_name}-eks"
  public_subnet_cidrs  = ["10.10.1.0/24", "10.10.2.0/24", "10.10.3.0/24"]
  private_subnet_cidrs = ["10.10.11.0/24", "10.10.12.0/24", "10.10.13.0/24"]
  tags                 = local.common_tags
}

################################################################################
# Security Group - Bastion
################################################################################
module "bastion_sg" {
  source = "../../../modules/security-group"

  name        = "${local.environment}-${local.project_name}-bastion-sg"
  description = "Security group for bastion host - SSH from internal only"
  vpc_id      = module.vpc.vpc_id
  environment = local.environment

  ingress_rules = [
    {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["10.10.0.0/16"]
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
