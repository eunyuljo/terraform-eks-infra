"""EKS Nodegroup 변경에 대한 위험도 분석 규칙."""

import re

from .base_rule import BaseRule, Finding, RiskLevel


class EksNodegroupRule(BaseRule):
    """AWS EKS Node Group 리소스 변경 분석 규칙.

    검출 항목:
    - 노드그룹 삭제(destroy) → HIGH
    - AMI/launch template 변경 → HIGH
    - instance_type 변경 → MEDIUM
    - scaling config 변경 → MEDIUM
    """

    @property
    def resource_types(self) -> list[str]:
        return [
            "aws_eks_node_group",
            "aws_launch_template",
        ]

    def evaluate(self, resource_change: dict) -> list[Finding]:
        findings: list[Finding] = []
        patch = resource_change.get("patch", "")
        file_path = resource_change.get("file_path", "")
        line_number = resource_change.get("line_number", 0)
        resource_type = resource_change.get("resource_type", "aws_eks_node_group")
        change_type = resource_change.get("change_type", "modified")

        # 노드그룹 삭제 감지
        if change_type == "removed" and resource_type == "aws_eks_node_group":
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message="EKS node group is being destroyed",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # AMI 변경 감지
        if self._has_ami_change(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message="AMI or image_id is being changed (may cause node replacement)",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # Launch template 변경 감지
        if self._has_launch_template_change(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message="Launch template version or configuration changed",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # instance_type 변경 감지
        if self._has_instance_type_change(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.MEDIUM,
                    message="Instance type is being changed",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # Scaling config 변경 감지
        if self._has_scaling_change(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.MEDIUM,
                    message="Scaling configuration changed (min/max/desired size)",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        return findings

    def _has_ami_change(self, patch: str) -> bool:
        """AMI ID 변경 감지."""
        for line in patch.split("\n"):
            if line.startswith("+") or line.startswith("-"):
                if re.search(r"(ami|image_id)\s*=", line, re.IGNORECASE):
                    return True
        return False

    def _has_launch_template_change(self, patch: str) -> bool:
        """Launch template 변경 감지."""
        for line in patch.split("\n"):
            if line.startswith("+") or line.startswith("-"):
                if re.search(
                    r"(launch_template|version)\s*=", line
                ) and "launch_template" in patch:
                    return True
        return False

    def _has_instance_type_change(self, patch: str) -> bool:
        """Instance type 변경 감지."""
        added = []
        removed = []
        for line in patch.split("\n"):
            if re.search(r"instance_type", line):
                if line.startswith("+"):
                    added.append(line)
                elif line.startswith("-"):
                    removed.append(line)
        # 기존 값이 제거되고 새 값이 추가되면 변경으로 판단
        return bool(added and removed)

    def _has_scaling_change(self, patch: str) -> bool:
        """Scaling config (min_size, max_size, desired_size) 변경 감지."""
        scaling_keywords = ["min_size", "max_size", "desired_size"]
        for line in patch.split("\n"):
            if line.startswith("+") or line.startswith("-"):
                for keyword in scaling_keywords:
                    if keyword in line:
                        return True
        return False
