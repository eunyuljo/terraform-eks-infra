"""네트워크 변경에 대한 위험도 분석 규칙."""

import re

from .base_rule import BaseRule, Finding, RiskLevel


class NetworkRule(BaseRule):
    """AWS 네트워크 리소스 변경 분석 규칙.

    검출 항목:
    - VPC CIDR 변경 → HIGH
    - NAT Gateway 삭제 → HIGH
    - Route table 변경 → MEDIUM
    - Subnet 추가/삭제 → MEDIUM
    """

    @property
    def resource_types(self) -> list[str]:
        return [
            "aws_vpc",
            "aws_subnet",
            "aws_nat_gateway",
            "aws_route_table",
            "aws_route",
            "aws_route_table_association",
            "aws_internet_gateway",
            "aws_eip",
        ]

    def evaluate(self, resource_change: dict) -> list[Finding]:
        findings: list[Finding] = []
        patch = resource_change.get("patch", "")
        file_path = resource_change.get("file_path", "")
        line_number = resource_change.get("line_number", 0)
        resource_type = resource_change.get("resource_type", "aws_vpc")
        change_type = resource_change.get("change_type", "modified")

        # VPC CIDR 변경 감지
        if resource_type == "aws_vpc" and self._has_cidr_change(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message="VPC CIDR block is being changed (may cause connectivity issues)",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # NAT Gateway 삭제 감지
        if resource_type == "aws_nat_gateway" and change_type == "removed":
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message="NAT Gateway is being destroyed (will break private subnet internet access)",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # Route table 변경 감지
        if resource_type in ("aws_route_table", "aws_route") and change_type in (
            "modified",
            "added",
            "removed",
        ):
            findings.append(
                Finding(
                    risk_level=RiskLevel.MEDIUM,
                    message=f"Route table configuration changed ({change_type})",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # Subnet 추가/삭제 감지
        if resource_type == "aws_subnet" and change_type in ("added", "removed"):
            findings.append(
                Finding(
                    risk_level=RiskLevel.MEDIUM,
                    message=f"Subnet is being {change_type}",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        return findings

    def _has_cidr_change(self, patch: str) -> bool:
        """CIDR block 변경 감지."""
        added_cidr = False
        removed_cidr = False
        for line in patch.split("\n"):
            if re.search(r"cidr_block\s*=", line):
                if line.startswith("+"):
                    added_cidr = True
                elif line.startswith("-"):
                    removed_cidr = True
        return added_cidr and removed_cidr
