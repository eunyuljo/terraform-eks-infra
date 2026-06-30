terraform {
  backend "s3" {
    bucket         = "myproject-terraform-state"
    key            = "prod/network/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "myproject-terraform-lock"
    encrypt        = true
  }
}
