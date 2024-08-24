from githubkit import AppInstallationAuthStrategy, GitHub, Response
from githubkit.versions.latest.models import (
    FullRepository,
    Issue,
    IssueComment,
    PullRequest,
    PullRequestSimple,
)
from loguru import logger

from tux.utils.constants import Constants as CONST


class GithubService:
    def __init__(self) -> None:
        self.github = GitHub(
            AppInstallationAuthStrategy(
                CONST.GITHUB_APP_ID,
                CONST.GITHUB_PRIVATE_KEY,
                int(CONST.GITHUB_INSTALLATION_ID),
                CONST.GITHUB_CLIENT_ID,
                CONST.GITHUB_CLIENT_SECRET,
            ),
        )

    async def get_repo(self) -> FullRepository:
        try:
            response: Response[FullRepository] = await self.github.rest.repos.async_get(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
            )

            repo: FullRepository = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching repository: {e}")
            raise

        else:
            return repo

    async def create_issue(self, title: str, body: str) -> Issue:
        try:
            response: Response[Issue] = await self.github.rest.issues.async_create(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                title=title,
                body=body,
            )

            created_issue = response.parsed_data

        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            raise

        else:
            return created_issue

    async def create_issue_comment(self, issue_number: int, body: str) -> IssueComment:
        try:
            response: Response[IssueComment] = await self.github.rest.issues.async_create_comment(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                issue_number,
                body=body,
            )

            created_issue_comment = response.parsed_data

        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            raise

        else:
            return created_issue_comment

    async def close_issue(self, issue_number: int) -> Issue:
        try:
            response: Response[Issue] = await self.github.rest.issues.async_update(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                issue_number,
                state="closed",
            )

            closed_issue = response.parsed_data

        except Exception as e:
            logger.error(f"Error closing issue: {e}")
            raise

        else:
            return closed_issue

    async def get_issue(self, issue_number: int) -> Issue:
        try:
            response: Response[Issue] = await self.github.rest.issues.async_get(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                issue_number,
            )

            issue = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching issue: {e}")
            raise

        else:
            return issue

    async def get_open_issues(self) -> list[Issue]:
        try:
            response: Response[list[Issue]] = await self.github.rest.issues.async_list_for_repo(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                state="open",
            )

            open_issues = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            raise

        else:
            return open_issues

    async def get_closed_issues(self) -> list[Issue]:
        try:
            response: Response[list[Issue]] = await self.github.rest.issues.async_list_for_repo(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                state="closed",
            )

            closed_issues = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            raise

        else:
            return closed_issues

    async def get_open_pulls(self) -> list[PullRequestSimple]:
        try:
            response: Response[list[PullRequestSimple]] = await self.github.rest.pulls.async_list(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                state="open",
            )

            open_pulls = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching PRs: {e}")
            raise

        else:
            return open_pulls

    async def get_closed_pulls(self) -> list[PullRequestSimple]:
        try:
            response: Response[list[PullRequestSimple]] = await self.github.rest.pulls.async_list(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                state="closed",
            )

            closed_pulls = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching PRs: {e}")
            raise

        else:
            return closed_pulls

    async def get_pull(self, pr_number: int) -> PullRequest:
        try:
            response: Response[PullRequest] = await self.github.rest.pulls.async_get(
                CONST.GITHUB_REPO_OWNER,
                CONST.GITHUB_REPO,
                pr_number,
            )

            pull = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching PR: {e}")
            raise

        else:
            return pull
