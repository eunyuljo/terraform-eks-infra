"""PR Review Checker Rules - Terraform 리소스별 위험도 분석 규칙."""

from .base_rule import BaseRule, Finding, RiskLevel
from .security_group import SecurityGroupRule
from .eks_nodegroup import EksNodegroupRule
from .iam import IamRule
from .network import NetworkRule

ALL_RULES = [
    SecurityGroupRule(),
    EksNodegroupRule(),
    IamRule(),
    NetworkRule(),
]

__all__ = [
    "BaseRule",
    "Finding",
    "RiskLevel",
    "SecurityGroupRule",
    "EksNodegroupRule",
    "IamRule",
    "NetworkRule",
    "ALL_RULES",
]
