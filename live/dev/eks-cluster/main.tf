################################################################################
# Dev - EKS Cluster
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

################################################################################
# IRSA - AWS Load Balancer Controller
################################################################################
locals {
  oidc_issuer_url = replace(module.eks.cluster_oidc_issuer_url, "https://", "")
}

data "aws_caller_identity" "current" {}

module "irsa_alb_controller" {
  source = "../../../modules/irsa-role"

  environment          = var.environment
  project_name         = var.project_name
  service_name         = "alb-controller"
  namespace            = "kube-system"
  service_account_name = "aws-load-balancer-controller"
  oidc_provider_arn    = module.eks.oidc_provider_arn
  oidc_issuer_url      = local.oidc_issuer_url
  policy_arns          = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/AWSLoadBalancerControllerIAMPolicy"]
  tags                 = local.common_tags
}

################################################################################
# IRSA - Cluster Autoscaler
################################################################################
module "irsa_cluster_autoscaler" {
  source = "../../../modules/irsa-role"

  environment          = var.environment
  project_name         = var.project_name
  service_name         = "cluster-autoscaler"
  namespace            = "kube-system"
  service_account_name = "cluster-autoscaler"
  oidc_provider_arn    = module.eks.oidc_provider_arn
  oidc_issuer_url      = local.oidc_issuer_url
  tags                 = local.common_tags

  inline_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "autoscaling:DescribeTags",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:DescribeImages",
          "ec2:GetInstanceTypesFromInstanceRequirements",
          "eks:DescribeNodegroup"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "autoscaling:ResourceTag/kubernetes.io/cluster/${var.environment}-${var.project_name}-eks" = "owned"
          }
        }
      }
    ]
  })
}

################################################################################
# IRSA - External DNS
################################################################################
module "irsa_external_dns" {
  source = "../../../modules/irsa-role"

  environment          = var.environment
  project_name         = var.project_name
  service_name         = "external-dns"
  namespace            = "kube-system"
  service_account_name = "external-dns"
  oidc_provider_arn    = module.eks.oidc_provider_arn
  oidc_issuer_url      = local.oidc_issuer_url
  tags                 = local.common_tags

  inline_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["route53:ChangeResourceRecordSets"]
        Resource = "arn:aws:route53:::hostedzone/*"
      },
      {
        Effect = "Allow"
        Action = [
          "route53:ListHostedZones",
          "route53:ListResourceRecordSets",
          "route53:ListTagsForResource"
        ]
        Resource = "*"
      }
    ]
  })
}
