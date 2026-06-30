terraform {
  backend "s3" {
    bucket         = "myproject-terraform-state-977099011692"
    key            = "prod/eks-cluster/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "myproject-terraform-lock"
    encrypt        = true
  }
}
