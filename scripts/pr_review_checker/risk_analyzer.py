"""위험도 분석 모듈.

파싱된 리소스 변경 정보를 규칙 엔진으로 평가하여 전체 PR 위험도를 결정한다.
"""

from dataclasses import dataclass, field

from .diff_parser import ParseResult
from .rules import ALL_RULES, Finding, RiskLevel


@dataclass
class AnalysisResult:
    """분석 결과."""

    findings: list[Finding] = field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.LOW
    required_approvers: str = ""
    lifecycles: set[str] = field(default_factory=set)
    environments: set[str] = field(default_factory=set)
    total_tf_files: int = 0

    @property
    def findings_by_category(self) -> dict[str, list[Finding]]:
        """리소스 타입별 findings 그룹핑."""
        categories: dict[str, list[Finding]] = {}
        for finding in self.findings:
            category = self._categorize(finding.resource_type)
            if category not in categories:
                categories[category] = []
            categories[category].append(finding)
        return categories

    @property
    def risk_counts(self) -> dict[str, int]:
        """위험도별 카운트."""
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for finding in self.findings:
            counts[finding.risk_level.value] += 1
        return counts

    @staticmethod
    def _categorize(resource_type: str) -> str:
        """리소스 타입을 카테고리로 분류."""
        sg_types = [
            "aws_security_group", "aws_security_group_rule",
            "aws_vpc_security_group_ingress_rule",
            "aws_vpc_security_group_egress_rule",
        ]
        eks_types = ["aws_eks_node_group", "aws_launch_template"]
        iam_types = [
            "aws_iam_role", "aws_iam_role_policy",
            "aws_iam_role_policy_attachment",
            "aws_iam_policy", "aws_iam_policy_document",
        ]
        network_types = [
            "aws_vpc", "aws_subnet", "aws_nat_gateway",
            "aws_route_table", "aws_route",
            "aws_route_table_association",
            "aws_internet_gateway", "aws_eip",
        ]

        if resource_type in sg_types:
            return "Security Group"
        elif resource_type in eks_types:
            return "EKS Nodegroup"
        elif resource_type in iam_types:
            return "IAM"
        elif resource_type in network_types:
            return "Network"
        else:
            return "Other"


def analyze(parse_result: ParseResult) -> AnalysisResult:
    """파싱 결과를 분석하여 AnalysisResult를 반환한다."""
    all_findings: list[Finding] = []

    for resource_change in parse_result.resource_changes:
        change_dict = resource_change.to_dict()
        resource_type = change_dict["resource_type"]

        for rule in ALL_RULES:
            if resource_type in rule.resource_types:
                findings = rule.evaluate(change_dict)
                all_findings.extend(findings)

    overall_risk = _determine_overall_risk(all_findings, parse_result.environments)
    required_approvers = _determine_required_approvers(overall_risk)

    return AnalysisResult(
        findings=all_findings,
        overall_risk=overall_risk,
        required_approvers=required_approvers,
        lifecycles=parse_result.lifecycles,
        environments=parse_result.environments,
        total_tf_files=parse_result.total_tf_files,
    )


def _determine_overall_risk(
    findings: list[Finding], environments: set[str]
) -> RiskLevel:
    """전체 위험도를 결정한다."""
    if not findings:
        return RiskLevel.LOW

    max_risk = max(f.risk_level for f in findings)

    # prod 환경이면 MEDIUM -> HIGH로 상승
    if "prod" in environments and max_risk == RiskLevel.MEDIUM:
        max_risk = RiskLevel.HIGH

    return max_risk


def _determine_required_approvers(risk_level: RiskLevel) -> str:
    """위험도에 따른 필요 승인자를 결정한다."""
    approvers = {
        RiskLevel.HIGH: "Senior Engineer + Customer Approval",
        RiskLevel.MEDIUM: "Senior Engineer",
        RiskLevel.LOW: "1 Team Member",
    }
    return approvers[risk_level]
