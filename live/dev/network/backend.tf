terraform {
  backend "s3" {
    bucket         = "myproject-terraform-state"
    key            = "dev/network/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "myproject-terraform-lock"
    encrypt        = true
  }
}
