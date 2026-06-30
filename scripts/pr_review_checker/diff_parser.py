"""PR diff 파싱 모듈.

GitHub API에서 받은 PR files diff를 파싱하여 Terraform 리소스 변경 정보를 추출한다.
"""

import re
from dataclasses import dataclass, field


@dataclass
class ResourceChange:
    """파싱된 Terraform 리소스 변경 정보."""

    resource_type: str
    resource_name: str
    file_path: str
    change_type: str  # "added", "removed", "modified"
    patch: str
    line_number: int = 0
    lifecycle: str = ""
    environment: str = ""

    def to_dict(self) -> dict:
        """규칙 엔진에 전달할 dict 변환."""
        return {
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "file_path": self.file_path,
            "change_type": self.change_type,
            "patch": self.patch,
            "line_number": self.line_number,
            "lifecycle": self.lifecycle,
            "environment": self.environment,
        }


@dataclass
class ParseResult:
    """전체 파싱 결과."""

    resource_changes: list[ResourceChange] = field(default_factory=list)
    lifecycles: set[str] = field(default_factory=set)
    environments: set[str] = field(default_factory=set)
    total_tf_files: int = 0


# Terraform resource 블록 패턴
RESOURCE_PATTERN = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"')

# 라이프사이클 판별 패턴
LIFECYCLE_PATTERNS = {
    "network": re.compile(r"(^|/)network/"),
    "eks-cluster": re.compile(r"(^|/)eks-cluster/"),
    "modules/vpc": re.compile(r"(^|/)modules/vpc/"),
    "modules/eks": re.compile(r"(^|/)modules/eks/"),
    "modules/security-group": re.compile(r"(^|/)modules/security-group/"),
}

# 환경 판별 패턴 (live/{env}/ 구조)
ENVIRONMENT_PATTERNS = {
    "prod": re.compile(r"(^|/)live/prod/"),
    "stg": re.compile(r"(^|/)live/stg/"),
    "dev": re.compile(r"(^|/)live/dev/"),
}


def parse_pr_files(pr_files: list) -> ParseResult:
    """PR files 목록을 파싱하여 리소스 변경 정보를 추출한다."""
    result = ParseResult()

    for pr_file in pr_files:
        filename = _get_filename(pr_file)
        patch = _get_patch(pr_file)
        status = _get_status(pr_file)

        # .tf 파일만 필터
        if not filename.endswith(".tf"):
            continue

        result.total_tf_files += 1

        # 라이프사이클 판별
        lifecycle = _detect_lifecycle(filename)
        if lifecycle:
            result.lifecycles.add(lifecycle)

        # 환경 판별
        environment = _detect_environment(filename)
        if environment:
            result.environments.add(environment)

        # 패치가 없으면 스킵
        if not patch:
            continue

        # 리소스 블록 변경 감지
        resource_changes = _extract_resource_changes(
            patch=patch,
            filename=filename,
            file_status=status,
            lifecycle=lifecycle,
            environment=environment,
        )
        result.resource_changes.extend(resource_changes)

    return result


def _extract_resource_changes(
    patch: str,
    filename: str,
    file_status: str,
    lifecycle: str,
    environment: str,
) -> list[ResourceChange]:
    """패치에서 리소스 변경을 추출한다."""
    changes: list[ResourceChange] = []
    lines = patch.split("\n")

    current_line = 0
    for i, line in enumerate(lines):
        # @@ hunk header에서 라인 번호 추출
        hunk_match = re.match(r"^@@\s*-\d+(?:,\d+)?\s+\+(\d+)", line)
        if hunk_match:
            current_line = int(hunk_match.group(1))
            continue

        # resource 블록 감지
        resource_match = RESOURCE_PATTERN.search(line)
        if resource_match:
            resource_type = resource_match.group(1)
            resource_name = resource_match.group(2)
            change_type = _determine_change_type(line, file_status)
            resource_patch = _collect_resource_patch(lines, i)

            changes.append(
                ResourceChange(
                    resource_type=resource_type,
                    resource_name=resource_name,
                    file_path=filename,
                    change_type=change_type,
                    patch=resource_patch,
                    line_number=current_line,
                    lifecycle=lifecycle,
                    environment=environment,
                )
            )

        if not line.startswith("-"):
            current_line += 1

    # 리소스 블록 없이도 변경된 리소스 타입을 추론
    if not changes:
        inferred = _infer_resource_changes(
            patch, filename, file_status, lifecycle, environment
        )
        changes.extend(inferred)

    return changes


def _collect_resource_patch(lines: list[str], start_idx: int) -> str:
    """리소스 블록의 시작부터 관련 라인을 수집한다."""
    collected = []
    brace_count = 0
    started = False

    for i in range(start_idx, min(start_idx + 100, len(lines))):
        line = lines[i]
        collected.append(line)
        clean_line = line.lstrip("+-")
        brace_count += clean_line.count("{") - clean_line.count("}")

        if "{" in clean_line:
            started = True
        if started and brace_count <= 0:
            break

    return "\n".join(collected)


def _infer_resource_changes(
    patch: str,
    filename: str,
    file_status: str,
    lifecycle: str,
    environment: str,
) -> list[ResourceChange]:
    """패치 내용에서 리소스 타입을 추론한다."""
    changes: list[ResourceChange] = []
    inferred_types: set[str] = set()

    resource_indicators = {
        "aws_security_group": ["ingress", "egress", "security_group"],
        "aws_vpc": ["cidr_block", "vpc_id", "aws_vpc"],
        "aws_subnet": ["subnet", "availability_zone"],
        "aws_iam_role": ["assume_role_policy", "iam_role"],
        "aws_eks_node_group": ["node_group", "scaling_config"],
        "aws_nat_gateway": ["nat_gateway", "allocation_id"],
    }

    for resource_type, indicators in resource_indicators.items():
        for indicator in indicators:
            if indicator in patch.lower():
                inferred_types.add(resource_type)
                break

    for resource_type in inferred_types:
        change_type = "modified"
        if file_status == "added":
            change_type = "added"
        elif file_status == "removed":
            change_type = "removed"

        changes.append(
            ResourceChange(
                resource_type=resource_type,
                resource_name="inferred",
                file_path=filename,
                change_type=change_type,
                patch=patch,
                line_number=0,
                lifecycle=lifecycle,
                environment=environment,
            )
        )

    return changes


def _determine_change_type(line: str, file_status: str) -> str:
    """변경 유형을 판별한다."""
    if file_status == "added":
        return "added"
    if file_status == "removed":
        return "removed"
    if line.startswith("+"):
        return "added"
    if line.startswith("-"):
        return "removed"
    return "modified"


def _detect_lifecycle(filepath: str) -> str:
    """파일 경로에서 라이프사이클을 판별한다."""
    for lifecycle, pattern in LIFECYCLE_PATTERNS.items():
        if pattern.search(filepath):
            return lifecycle
    return ""


def _detect_environment(filepath: str) -> str:
    """파일 경로에서 환경을 판별한다."""
    for env, pattern in ENVIRONMENT_PATTERNS.items():
        if pattern.search(filepath):
            return env
    return ""


def _get_filename(pr_file) -> str:
    """PR file 객체에서 filename을 안전하게 추출."""
    if isinstance(pr_file, dict):
        return pr_file.get("filename", "")
    return getattr(pr_file, "filename", "")


def _get_patch(pr_file) -> str:
    """PR file 객체에서 patch를 안전하게 추출."""
    if isinstance(pr_file, dict):
        return pr_file.get("patch", "")
    return getattr(pr_file, "patch", "") or ""


def _get_status(pr_file) -> str:
    """PR file 객체에서 status를 안전하게 추출."""
    if isinstance(pr_file, dict):
        return pr_file.get("status", "modified")
    return getattr(pr_file, "status", "modified")
