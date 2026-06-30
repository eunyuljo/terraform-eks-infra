"""Base rule abstract class and data models for PR review checker."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """위험도 레벨."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    def __lt__(self, other: "RiskLevel") -> bool:
        order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
        return order[self] < order[other]

    def __le__(self, other: "RiskLevel") -> bool:
        order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
        return order[self] <= order[other]

    def __gt__(self, other: "RiskLevel") -> bool:
        order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
        return order[self] > order[other]

    def __ge__(self, other: "RiskLevel") -> bool:
        order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
        return order[self] >= order[other]


@dataclass
class Finding:
    """분석 결과 항목."""

    risk_level: RiskLevel
    message: str
    resource_type: str
    file_path: str
    line_number: int = 0


class BaseRule(ABC):
    """리소스 분석 규칙 추상 베이스 클래스."""

    @abstractmethod
    def evaluate(self, resource_change: dict) -> list[Finding]:
        """리소스 변경을 평가하여 Finding 목록을 반환한다.

        Args:
            resource_change: 파싱된 리소스 변경 정보 dict.
                Keys: resource_type, file_path, change_type, patch, line_number

        Returns:
            Finding 목록.
        """
        pass

    @property
    @abstractmethod
    def resource_types(self) -> list[str]:
        """이 규칙이 적용되는 Terraform 리소스 타입 목록."""
        pass
