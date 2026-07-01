"""
GitHub data fetcher service.
Uses PyGithub for REST API (issues, PRs, contributors)
and httpx for GraphQL API (discussions).
"""
import re
import os
import logging
from typing import Any
from github import Github, GithubException
from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
from app.utils.github_graphql import fetch_discussions_graphql

logger = logging.getLogger(__name__)
settings = get_settings()


class GitHubFetcher:
    """Fetches repository data from the GitHub API."""

    def __init__(self, token: str | None = None):
        # Force read from os.environ to bypass any pydantic caching issues
        env_token = os.environ.get("GITHUB_TOKEN", "")
        self.token = token or env_token or settings.GITHUB_TOKEN
        if not self.token:
            logger.error("GITHUB_TOKEN is still empty! Reading directly from file...")
            try:
                with open(".env", "r") as f:
                    for line in f:
                        if line.startswith("GITHUB_TOKEN="):
                            self.token = line.split("=", 1)[1].strip()
            except Exception:
                pass
                
        # Increase pool_size to handle concurrent requests from asyncio.gather
        self.github = Github(self.token, per_page=100, pool_size=20)

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Extract owner and repo name from a GitHub URL."""
        pattern = r"github\.com/([^/]+)/([^/\s#?]+)"
        match = re.search(pattern, url.rstrip("/"))
        if not match:
            raise ValueError(f"Invalid GitHub repository URL: {url}")
        owner = match.group(1)
        name = match.group(2).removesuffix(".git")
        return owner, name

    def fetch_repo_metadata(self, owner: str, name: str) -> dict[str, Any]:
        """Fetch basic repository metadata."""
        repo = self.github.get_repo(f"{owner}/{name}")
        return {
            "owner": owner,
            "name": name,
            "description": repo.description or "",
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "language": repo.language,
            "topics": repo.get_topics(),
            "default_branch": repo.default_branch,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "html_url": repo.html_url,
        }

    def fetch_readme(self, owner: str, name: str) -> str:
        """Fetch README content as text."""
        repo = self.github.get_repo(f"{owner}/{name}")
        try:
            readme = repo.get_readme()
            return readme.decoded_content.decode("utf-8")
        except GithubException:
            logger.warning(f"No README found for {owner}/{name}")
            return ""

    def fetch_issues(self, owner: str, name: str, limit: int | None = None) -> list[dict]:
        """Fetch issues with comments. Returns structured dicts."""
        limit = limit or settings.MAX_ISSUES
        repo = self.github.get_repo(f"{owner}/{name}")
        issues_data = []

        for i, issue in enumerate(repo.get_issues(state="all", sort="updated", direction="desc")):
            if i >= limit:
                break
            if issue.pull_request:
                continue  # Skip PRs (GitHub API returns PRs as issues)

            # Fetch comments for this issue
            comments = []
            try:
                for comment in issue.get_comments():
                    comments.append({
                        "author": comment.user.login if comment.user else "unknown",
                        "body": comment.body or "",
                        "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    })
            except GithubException:
                pass

            issues_data.append({
                "number": issue.number,
                "title": issue.title,
                "body": issue.body or "",
                "state": issue.state,
                "author": issue.user.login if issue.user else "unknown",
                "labels": [label.name for label in issue.labels],
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                "comments": comments,
                "comment_count": issue.comments,
                "html_url": issue.html_url,
            })

        return issues_data

    def fetch_pull_requests(self, owner: str, name: str, limit: int | None = None) -> list[dict]:
        """Fetch pull requests with reviews."""
        limit = limit or settings.MAX_PRS
        repo = self.github.get_repo(f"{owner}/{name}")
        prs_data = []

        for i, pr in enumerate(repo.get_pulls(state="all", sort="updated", direction="desc")):
            if i >= limit:
                break

            # Fetch reviews
            reviews = []
            try:
                for review in pr.get_reviews():
                    reviews.append({
                        "author": review.user.login if review.user else "unknown",
                        "state": review.state,
                        "body": review.body or "",
                        "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None,
                    })
            except GithubException:
                pass

            prs_data.append({
                "number": pr.number,
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "merged": pr.merged,
                "author": pr.user.login if pr.user else "unknown",
                "labels": [label.name for label in pr.labels],
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                "reviews": reviews,
                "review_comments": pr.review_comments,
                "html_url": pr.html_url,
                "files_changed": pr.changed_files,
                "additions": pr.additions,
                "deletions": pr.deletions,
            })

        return prs_data

    def fetch_contributors(self, owner: str, name: str) -> list[dict]:
        """Fetch contributor list with stats."""
        repo = self.github.get_repo(f"{owner}/{name}")
        contributors = []

        try:
            for contributor in repo.get_contributors():
                contributors.append({
                    "username": contributor.login,
                    "avatar_url": contributor.avatar_url,
                    "contributions": contributor.contributions,
                    "html_url": contributor.html_url,
                })
        except GithubException:
            logger.warning(f"Could not fetch contributors for {owner}/{name}")

        return contributors

    async def fetch_discussions(self, owner: str, name: str, limit: int | None = None) -> list[dict]:
        """Fetch discussions via GraphQL API."""
        limit = limit or settings.MAX_DISCUSSIONS
        return await fetch_discussions_graphql(
            owner=owner,
            name=name,
            token=self.token,
            limit=limit,
        )

    def fetch_file_content(self, owner: str, name: str, file_path: str) -> str:
        """Fetch the content of a specific file."""
        repo = self.github.get_repo(f"{owner}/{name}")
        try:
            file_content = repo.get_contents(file_path)
            # PyGithub get_contents can return a list if the path is a dir, handle carefully
            if isinstance(file_content, list):
                return ""
            return file_content.decoded_content.decode("utf-8")
        except GithubException:
            return ""

    def fetch_top_level_structure(self, owner: str, name: str) -> list[str]:
        """Fetch the top-level directory and file structure."""
        repo = self.github.get_repo(f"{owner}/{name}")
        structure = []
        try:
            contents = repo.get_contents("")
            # Handle PyGithub returning a single ContentFile if repo is empty, though unlikely
            if not isinstance(contents, list):
                contents = [contents]
            for item in contents:
                item_type = "dir" if item.type == "dir" else "file"
                structure.append(f"[{item_type}] {item.path}")
        except GithubException:
            pass
        return structure

    def fetch_releases(self, owner: str, name: str, limit: int = 10) -> list[dict]:
        """Fetch recent releases."""
        repo = self.github.get_repo(f"{owner}/{name}")
        releases = []
        try:
            for i, release in enumerate(repo.get_releases()):
                if i >= limit:
                    break
                releases.append({
                    "tag_name": release.tag_name,
                    "name": release.title,
                    "body": release.body or "",
                    "created_at": release.created_at.isoformat() if release.created_at else None,
                    "published_at": release.published_at.isoformat() if release.published_at else None,
                })
        except GithubException:
            pass
        return releases

    def fetch_latest_commit_sha(self, owner: str, name: str) -> str:
        """Fetch the latest commit SHA of the default branch of the repository."""
        try:
            repo = self.github.get_repo(f"{owner}/{name}")
            return repo.get_branch(repo.default_branch).commit.sha
        except Exception as e:
            logger.error(f"Failed to fetch latest commit SHA: {e}")
            return ""

