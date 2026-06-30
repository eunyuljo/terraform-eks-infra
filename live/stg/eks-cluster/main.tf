################################################################################
# Stg - EKS Cluster
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
# Remote State - Network
################################################################################
data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = "${var.environment}/network/terraform.tfstate"
    region = var.aws_region
  }
}

################################################################################
# EKS Cluster
################################################################################
module "eks" {
  source = "../../../modules/eks"

  cluster_name       = "${var.project_name}-eks"
  cluster_version    = var.cluster_version
  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  subnet_ids         = data.terraform_remote_state.network.outputs.private_subnet_ids
  node_instance_type = var.node_instance_type
  node_min_size      = var.node_min_size
  node_max_size      = var.node_max_size
  node_desired_size  = var.node_desired_size
  environment        = var.environment
  tags               = local.common_tags
}
