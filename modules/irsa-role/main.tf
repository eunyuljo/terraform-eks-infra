################################################################################
# IRSA Role Module
#
# EKS ServiceAccount에 연결할 IAM Role을 생성합니다.
# 사용 시 서비스명, namespace, serviceaccount명만 지정하면 됩니다.
################################################################################

data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_issuer_url}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${var.service_account_name}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_issuer_url}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [var.oidc_provider_arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "this" {
  name               = "${var.environment}-${var.project_name}-${var.service_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "this" {
  count = length(var.policy_arns)

  policy_arn = var.policy_arns[count.index]
  role       = aws_iam_role.this.name
}

resource "aws_iam_policy" "inline" {
  count = var.inline_policy != null ? 1 : 0

  name        = "${var.environment}-${var.project_name}-${var.service_name}-policy"
  description = "IAM policy for ${var.service_name}"
  policy      = var.inline_policy
  tags        = var.tags
}

resource "aws_iam_role_policy_attachment" "inline" {
  count = var.inline_policy != null ? 1 : 0

  policy_arn = aws_iam_policy.inline[0].arn
  role       = aws_iam_role.this.name
}
