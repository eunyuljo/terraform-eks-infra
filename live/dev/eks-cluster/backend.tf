terraform {
  backend "s3" {
    bucket         = "myproject-terraform-state"
    key            = "dev/eks-cluster/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "myproject-terraform-lock"
    encrypt        = true
  }
}
