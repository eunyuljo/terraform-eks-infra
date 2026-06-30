"""PR Review Checker - CLI 진입점.

Terraform PR의 변경사항을 분석하여 위험도 체크리스트를 생성한다.

사용법:
    python -m pr_review_checker --dry-run
    python -m pr_review_checker

환경변수:
    GITHUB_TOKEN: GitHub Personal Access Token
    REPO: Repository (owner/name)
    PR_NUMBER: Pull Request 번호
"""

import argparse
import os
import sys

from dotenv import load_dotenv


def get_env_or_exit(name: str) -> str:
    """환경변수를 가져오거나, 없으면 에러 메시지와 함께 종료."""
    value = os.environ.get(name)
    if not value:
        print(
            f"Error: Environment variable '{name}' is required but not set.",
            file=sys.stderr,
        )
        print(f"Set it with: export {name}=<value>", file=sys.stderr)
        sys.exit(1)
    return value


def parse_args() -> argparse.Namespace:
    """CLI 인자를 파싱한다."""
    parser = argparse.ArgumentParser(
        description="Terraform PR Review Checker - "
        "Analyze PR changes and generate risk checklist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  GITHUB_TOKEN    GitHub Personal Access Token (required)
  REPO            Repository in owner/name format (required)
  PR_NUMBER       Pull Request number (required)

Examples:
  # Dry run (print checklist without posting)
  export GITHUB_TOKEN=ghp_xxx
  export REPO=myorg/terraform-eks-infra
  export PR_NUMBER=42
  python -m pr_review_checker --dry-run

  # Post comment to PR
  python -m pr_review_checker
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print checklist to stdout without posting to GitHub",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    return parser.parse_args()


def main() -> int:
    """메인 실행 함수."""
    # .env 파일 로드
    load_dotenv()

    args = parse_args()

    # 환경변수 확인
    token = get_env_or_exit("GITHUB_TOKEN")
    repo_name = get_env_or_exit("REPO")
    pr_number_str = get_env_or_exit("PR_NUMBER")

    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print(
            f"Error: PR_NUMBER must be an integer, got '{pr_number_str}'",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(f"Analyzing PR #{pr_number} in {repo_name}...")

    # 1. GitHub에서 PR diff 가져오기
    from .github_client import GitHubClient

    try:
        client = GitHubClient(token=token, repo_name=repo_name)
        pr_files = client.get_pr_files(pr_number)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error fetching PR: {e}", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Found {len(pr_files)} changed files")

    # 2. Diff 파싱
    from .diff_parser import parse_pr_files

    parse_result = parse_pr_files(pr_files)

    if args.verbose:
        print(f"Terraform files: {parse_result.total_tf_files}")
        print(f"Resource changes: {len(parse_result.resource_changes)}")
        print(f"Lifecycles: {parse_result.lifecycles}")
        print(f"Environments: {parse_result.environments}")

    # 3. 위험도 분석
    from .risk_analyzer import analyze

    analysis_result = analyze(parse_result)

    if args.verbose:
        print(f"Findings: {len(analysis_result.findings)}")
        print(f"Overall risk: {analysis_result.overall_risk.value}")

    # 4. 체크리스트 생성
    from .checklist_generator import generate_checklist

    checklist = generate_checklist(analysis_result)

    # 5. 결과 출력 또는 코멘트 게시
    if args.dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN - Checklist output:")
        print("=" * 60 + "\n")
        print(checklist)
        print("=" * 60)
        print("(Comment was NOT posted to GitHub)")
    else:
        try:
            client.post_comment(pr_number, checklist)
            print(f"Successfully posted review checklist to PR #{pr_number}")
        except Exception as e:
            print(f"Error posting comment: {e}", file=sys.stderr)
            # 실패해도 체크리스트는 출력
            print("\nGenerated checklist:")
            print(checklist)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
