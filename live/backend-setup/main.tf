################################################################################
# Terraform State Backend Setup
#
# 이 모듈은 다른 모든 Terraform 모듈의 state를 저장할 S3 버킷과
# state locking을 위한 DynamoDB 테이블을 생성합니다.
#
# 주의: 이 모듈의 state는 로컬에 저장됩니다 (terraform.tfstate)
#       이 파일은 git에 포함하지 않으며, 안전한 곳에 백업해야 합니다.
################################################################################

locals {
  aws_region     = var.aws_region
  bucket_name    = "${var.project_name}-terraform-state-${var.account_id}"
  dynamodb_table = "${var.project_name}-terraform-lock"
}

################################################################################
# S3 Bucket - State 저장소
################################################################################
resource "aws_s3_bucket" "state" {
  bucket = local.bucket_name

  # 실수로 삭제 방지
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = local.bucket_name
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

################################################################################
# DynamoDB Table - State Locking
################################################################################
resource "aws_dynamodb_table" "lock" {
  name         = local.dynamodb_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = local.dynamodb_table
  }
}
