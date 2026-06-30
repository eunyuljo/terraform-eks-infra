################################################################################
# Dev - EKS Cluster
################################################################################
locals {
  environment  = "dev"
  project_name = "myproject"
  owner        = "platform-team"

  common_tags = {
    Environment = local.environment
    ManagedBy   = "terraform"
    Project     = local.project_name
    Owner       = local.owner
  }
}

################################################################################
# Remote State - Network
################################################################################
data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "myproject-terraform-state"
    key    = "dev/network/terraform.tfstate"
    region = "ap-northeast-2"
  }
}

################################################################################
# EKS Cluster
################################################################################
module "eks" {
  source = "../../../modules/eks"

  cluster_name       = "${local.project_name}-eks"
  cluster_version    = "1.29"
  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  subnet_ids         = data.terraform_remote_state.network.outputs.private_subnet_ids
  node_instance_type = "m5.large"
  node_min_size      = 1
  node_max_size      = 3
  node_desired_size  = 2
  environment        = local.environment
  tags               = local.common_tags
}
