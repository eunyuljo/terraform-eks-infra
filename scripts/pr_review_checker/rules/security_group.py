"""Security Group 변경에 대한 위험도 분석 규칙."""

import re

from .base_rule import BaseRule, Finding, RiskLevel


class SecurityGroupRule(BaseRule):
    """AWS Security Group 리소스 변경 분석 규칙.

    검출 항목:
    - 0.0.0.0/0 ingress → HIGH
    - 포트 범위 0-65535 → HIGH
    - egress 전체 개방 → MEDIUM
    - description 미설정 → LOW
    """

    @property
    def resource_types(self) -> list[str]:
        return [
            "aws_security_group",
            "aws_security_group_rule",
            "aws_vpc_security_group_ingress_rule",
            "aws_vpc_security_group_egress_rule",
        ]

    def evaluate(self, resource_change: dict) -> list[Finding]:
        findings: list[Finding] = []
        patch = resource_change.get("patch", "")
        file_path = resource_change.get("file_path", "")
        line_number = resource_change.get("line_number", 0)
        resource_type = resource_change.get("resource_type", "aws_security_group")

        # 0.0.0.0/0 ingress 검출
        if self._has_open_ingress(patch):
            port_info = self._extract_port_info(patch)
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message=f"Ingress rule allows 0.0.0.0/0{port_info}",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # 포트 범위 0-65535 검출
        if self._has_full_port_range(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.HIGH,
                    message="Port range 0-65535 opens all ports",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # egress 전체 개방 검출
        if self._has_open_egress(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.MEDIUM,
                    message="Egress rule allows all outbound traffic (0.0.0.0/0)",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        # description 미설정 검출
        if self._missing_description(patch):
            findings.append(
                Finding(
                    risk_level=RiskLevel.LOW,
                    message="Security group rule missing description",
                    resource_type=resource_type,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        return findings

    def _has_open_ingress(self, patch: str) -> bool:
        """ingress 블록에서 0.0.0.0/0 또는 ::/0 CIDR 감지."""
        lines = patch.split("\n")
        in_ingress = False
        for line in lines:
            if not line.startswith("+"):
                if "ingress" in line:
                    in_ingress = True
                elif re.match(r"^\s*(egress|}\s*$)", line):
                    in_ingress = False
                continue
            # added line
            if "ingress" in line:
                in_ingress = True
            if "egress" in line:
                in_ingress = False
            if in_ingress and re.search(
                r'(cidr_blocks|cidr_ipv4)\s*=\s*.*"0\.0\.0\.0/0"', line
            ):
                return True
            if in_ingress and re.search(r'cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]', line):
                return True
            # Flat resource type check (aws_vpc_security_group_ingress_rule)
            if re.search(r'(cidr_ipv4|cidr_blocks)\s*=\s*.*"0\.0\.0\.0/0"', line):
                if "ingress" in patch.lower():
                    return True
        return False

    def _has_full_port_range(self, patch: str) -> bool:
        """포트 범위 0-65535 감지."""
        for line in patch.split("\n"):
            if not line.startswith("+"):
                continue
            if re.search(r"from_port\s*=\s*0", line):
                # from_port=0이 있으면 to_port=65535도 확인
                pass
            if re.search(r"to_port\s*=\s*65535", line):
                return True
        # from_port=0과 to_port=65535 조합 확인
        has_from_zero = bool(re.search(r"\+.*from_port\s*=\s*0", patch))
        has_to_all = bool(re.search(r"\+.*to_port\s*=\s*65535", patch))
        return has_from_zero and has_to_all

    def _has_open_egress(self, patch: str) -> bool:
        """egress 블록에서 0.0.0.0/0 감지."""
        lines = patch.split("\n")
        in_egress = False
        for line in lines:
            if "egress" in line:
                in_egress = True
            if in_egress and re.match(r"^\s*ingress", line):
                in_egress = False
            if in_egress and line.startswith("+") and re.search(
                r'(cidr_blocks|cidr_ipv4)\s*=\s*.*"0\.0\.0\.0/0"', line
            ):
                return True
        return False

    def _missing_description(self, patch: str) -> bool:
        """새로 추가된 리소스에 description이 없는지 확인."""
        added_lines = [l for l in patch.split("\n") if l.startswith("+")]
        if not added_lines:
            return False
        has_resource_def = any(
            "resource" in l or "ingress" in l or "egress" in l for l in added_lines
        )
        has_description = any("description" in l for l in added_lines)
        return has_resource_def and not has_description

    def _extract_port_info(self, patch: str) -> str:
        """패치에서 포트 정보 추출."""
        for line in patch.split("\n"):
            if line.startswith("+"):
                match = re.search(r"(from_port|to_port)\s*=\s*(\d+)", line)
                if match:
                    return f" on port {match.group(2)}"
        return ""
