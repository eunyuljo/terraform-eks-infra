"""GitHub API 연동 모듈.

PyGithub를 사용하여 PR diff를 가져오고, 분석 결과를 코멘트로 게시한다.
"""

import sys
from typing import Optional

try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = None

from .checklist_generator import BOT_SIGNATURE


class GitHubClient:
    """GitHub API 클라이언트."""

    def __init__(self, token: str, repo_name: str):
        if Github is None:
            raise ImportError(
                "PyGithub is not installed. "
                "Install it with: pip install PyGithub"
            )
        if not token:
            raise ValueError("GitHub token is required")
        if not repo_name or "/" not in repo_name:
            raise ValueError(
                "Repository name must be in 'owner/name' format"
            )

        self._github = Github(token)
        self._repo = self._github.get_repo(repo_name)

    def get_pr_files(self, pr_number: int) -> list:
        """PR의 변경 파일 목록을 가져온다."""
        try:
            pull = self._repo.get_pull(pr_number)
            return list(pull.get_files())
        except GithubException as e:
            print(f"Error fetching PR #{pr_number}: {e}", file=sys.stderr)
            raise

    def post_comment(self, pr_number: int, body: str) -> None:
        """PR에 코멘트를 게시한다. 기존 bot 코멘트가 있으면 업데이트."""
        try:
            pull = self._repo.get_pull(pr_number)
            existing_comment = self._find_bot_comment(pull)

            if existing_comment:
                existing_comment.edit(body)
                print(f"Updated existing comment on PR #{pr_number}")
            else:
                pull.create_issue_comment(body)
                print(f"Created new comment on PR #{pr_number}")
        except GithubException as e:
            print(
                f"Error posting comment on PR #{pr_number}: {e}",
                file=sys.stderr,
            )
            raise

    def _find_bot_comment(self, pull) -> Optional[object]:
        """PR에서 기존 bot 코멘트를 찾는다."""
        try:
            comments = pull.get_issue_comments()
            for comment in comments:
                if BOT_SIGNATURE in (comment.body or ""):
                    return comment
        except (GithubException, Exception):
            pass
        return None
