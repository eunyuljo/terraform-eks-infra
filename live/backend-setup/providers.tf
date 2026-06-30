terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # backend-setup은 local state 사용 (유일한 예외)
  # 이 모듈이 생성하는 S3/DynamoDB를 다른 모든 모듈이 backend로 사용합니다.
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      ManagedBy = "terraform"
      Purpose   = "terraform-state-backend"
    }
  }
}
