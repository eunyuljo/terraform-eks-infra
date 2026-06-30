"""IAM 변경에 대한 위험도 분석 규칙."""

import re

from .base_rule import BaseRule, Finding, RiskLevel


class IamRule(BaseRule):
    """AWS IAM 리소스 변경 분석 규칙.

    검출 항목:
    - AdministratorAccess 또는 Action "*" → HIGH
    - trust relationship 변경 → HIGH
    - 새 IAM Role 생성 → MEDIUM
    - IRSA 연결 변경 → MEDIUM
    """

    @property
    def resource_types(self) -> list[str]:
        return [
            "aws_iam_role",
            "aws_iam_role_policy",
            "aws_iam_role_policy_attachment",
            "aws_iam_policy",
            "aws_iam_policy_document",
        ]

    def evaluate(self, resource_change: dict) -> list[Finding]:
        findings: list[Finding] = []
        patch = resource_change.get("patch", "")
        file_path = resource_change.get("file_path", "")
        line_number = resource_change.get("line_number", 0)
        resource_type = resource_change.get("resource_type", "aws_iam_role")
        change_type = resource_change.get("change_type", "modified")

        # AdministratorAccess 또는 Action "*" 감지
        if self._has_admin_access(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message="AdministratorAccess or wildcard Action \"*\" detected",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # Trust relationship 변경 감지
        if self._has_trust_relationship_change(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message="IAM trust relationship (assume_role_policy) is being modified",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # 새 IAM Role 생성 감지
        if change_type == "added" and resource_type == "aws_iam_role":
            findings.append(
                Finding(
                    risk_level=RiskLevel.MEDIUM,
                    message="New IAM Role is being created",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # IRSA 연결 변경 감지
        if self._has_irsa_change(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.MEDIUM,
                    message="IRSA (IAM Roles for Service Accounts) configuration changed",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        return findings

    def _has_admin_access(self, patch: str) -> bool:
        """AdministratorAccess 정책 또는 Action \"*\" 감지."""
        for line in patch.split("\n"):
            if not line.startswith("+"):
                continue
            if "AdministratorAccess" in line:
                return True
            if re.search(r'[Aa]ction[s]?\s*=\s*.*"\*"', line):
                return True
            if re.search(r'"Action"\s*:\s*"\*"', line):
                return True
            if re.search(r'"Action"\s*:\s*\["\*"\]', line):
                return True
        return False

    def _has_trust_relationship_change(self, patch: str) -> bool:
        """Trust relationship (assume_role_policy) 변경 감지."""
        for line in patch.split("\n"):
            if line.startswith("+") or line.startswith("-"):
                if "assume_role_policy" in line:
                    return True
        return False

    def _has_irsa_change(self, patch: str) -> bool:
        """IRSA 관련 변경 감지."""
        irsa_indicators = [
            "oidc",
            "eks.amazonaws.com",
            "system:serviceaccount",
            "serviceaccount",
            "sts:AssumeRoleWithWebIdentity",
        ]
        for line in patch.split("\n"):
            if line.startswith("+") or line.startswith("-"):
                for indicator in irsa_indicators:
                    if indicator.lower() in line.lower():
                        return True
        return False
