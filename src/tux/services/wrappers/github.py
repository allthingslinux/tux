"""
GitHub API Service Wrapper for Tux Bot.

This module provides integration with the GitHub API using GitHub Apps authentication,
enabling the bot to interact with GitHub repositories, issues, pull requests, and more.
"""

from githubkit import AppInstallationAuthStrategy, GitHub, Response
from githubkit.versions.latest.models import (
    FullRepository,
    Issue,
    IssueComment,
    PullRequest,
    PullRequestSimple,
)

from tux.services.sentry import convert_httpx_error
from tux.shared.config import CONFIG


class GithubService:
    """GitHub API service wrapper for repository and issue management."""

    def __init__(self) -> None:
        """
        Initialize the GitHub service with app credentials.

        Raises
        ------
        ValueError
            If any required GitHub configuration is missing or invalid.
        """
        # Check if GitHub configuration is available
        if not CONFIG.EXTERNAL_SERVICES.GITHUB_APP_ID:
            msg = "GitHub App ID is not configured. Please set EXTERNAL_SERVICES__GITHUB_APP_ID in your .env file."
            raise ValueError(
                msg,
            )

        if not CONFIG.EXTERNAL_SERVICES.GITHUB_PRIVATE_KEY:
            msg = "GitHub private key is not configured. Please set EXTERNAL_SERVICES__GITHUB_PRIVATE_KEY in your .env file."
            raise ValueError(
                msg,
            )

        if not CONFIG.EXTERNAL_SERVICES.GITHUB_INSTALLATION_ID:
            msg = "GitHub installation ID is not configured. Please set EXTERNAL_SERVICES__GITHUB_INSTALLATION_ID in your .env file."
            raise ValueError(
                msg,
            )

        # Try to convert installation ID to int, with better error handling
        try:
            installation_id = int(CONFIG.EXTERNAL_SERVICES.GITHUB_INSTALLATION_ID)
        except ValueError as e:
            msg = "GitHub installation ID must be a valid integer. Please check EXTERNAL_SERVICES__GITHUB_INSTALLATION_ID in your .env file."
            raise ValueError(
                msg,
            ) from e

        self.github = GitHub(
            AppInstallationAuthStrategy(
                CONFIG.EXTERNAL_SERVICES.GITHUB_APP_ID,
                CONFIG.EXTERNAL_SERVICES.GITHUB_PRIVATE_KEY,
                installation_id,
                CONFIG.EXTERNAL_SERVICES.GITHUB_CLIENT_ID,
                CONFIG.EXTERNAL_SERVICES.GITHUB_CLIENT_SECRET,
            ),
        )

    async def get_repo(self) -> FullRepository:
        """
        Get the repository.

        Returns
        -------
        FullRepository
            The repository.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIPermissionError
            If insufficient permissions to access the repository.
        TuxAPIRequestError
            If the API request fails for other reasons.
        TuxAPIResourceNotFoundError
            If the repository is not found.
        """
        try:
            response: Response[FullRepository] = await self.github.rest.repos.async_get(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
            )

            repo: FullRepository = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="repos.get",
                not_found_resource=f"{CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER}/{CONFIG.EXTERNAL_SERVICES.GITHUB_REPO}",
            )
            raise  # Always raises, but needed for type checker

        else:
            return repo

    async def create_issue(self, title: str, body: str) -> Issue:
        """
        Create an issue.

        Parameters
        ----------
        title : str
            The title of the issue.
        body : str
            The body of the issue.

        Returns
        -------
        Issue
            The created issue.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIPermissionError
            If insufficient permissions.
        TuxAPIRequestError
            If the API request fails.
        """
        try:
            response: Response[Issue] = await self.github.rest.issues.async_create(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                title=title,
                body=body,
            )

            created_issue = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="issues.create",
            )
            raise  # Always raises, but needed for type checker

        else:
            return created_issue

    async def create_issue_comment(self, issue_number: int, body: str) -> IssueComment:
        """
        Create an issue comment.

        Parameters
        ----------
        issue_number : int
            The number of the issue.
        body : str
            The body of the comment.

        Returns
        -------
        IssueComment
            The created issue comment.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIPermissionError
            If insufficient permissions.
        TuxAPIRequestError
            If the API request fails.
        TuxAPIResourceNotFoundError
            If the issue is not found.
        """
        try:
            response: Response[
                IssueComment
            ] = await self.github.rest.issues.async_create_comment(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                issue_number,
                body=body,
            )

            created_issue_comment = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="issues.create_comment",
                not_found_resource=f"Issue #{issue_number}",
            )
            raise  # Always raises, but needed for type checker

        else:
            return created_issue_comment

    async def close_issue(self, issue_number: int) -> Issue:
        """
        Close an issue.

        Parameters
        ----------
        issue_number : int
            The number of the issue.

        Returns
        -------
        Issue
            The closed issue.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIPermissionError
            If insufficient permissions.
        TuxAPIRequestError
            If the API request fails.
        TuxAPIResourceNotFoundError
            If the issue is not found.
        """
        try:
            response: Response[Issue] = await self.github.rest.issues.async_update(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                issue_number,
                state="closed",
            )

            closed_issue = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="issues.update",
                not_found_resource=f"Issue #{issue_number}",
            )
            raise  # Always raises, but needed for type checker

        else:
            return closed_issue

    async def get_issue(self, issue_number: int) -> Issue:
        """
        Get an issue.

        Parameters
        ----------
        issue_number : int
            The number of the issue.

        Returns
        -------
        Issue
            The issue.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIRequestError
            If the API request fails.
        TuxAPIResourceNotFoundError
            If the issue is not found.
        """
        try:
            response: Response[Issue] = await self.github.rest.issues.async_get(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                issue_number,
            )

            issue = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="issues.get",
                not_found_resource=f"Issue #{issue_number}",
            )
            raise  # Always raises, but needed for type checker

        else:
            return issue

    async def get_open_issues(self) -> list[Issue]:
        """
        Get all open issues.

        Returns
        -------
        list[Issue]
            The list of open issues.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIRequestError
            If the API request fails.
        """
        try:
            response: Response[
                list[Issue]
            ] = await self.github.rest.issues.async_list_for_repo(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                state="open",
            )

            open_issues = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="issues.list_for_repo",
            )
            raise  # Always raises, but needed for type checker

        else:
            return open_issues

    async def get_closed_issues(self) -> list[Issue]:
        """
        Get all closed issues.

        Returns
        -------
        list[Issue]
            The list of closed issues.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIRequestError
            If the API request fails.
        """
        try:
            response: Response[
                list[Issue]
            ] = await self.github.rest.issues.async_list_for_repo(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                state="closed",
            )

            closed_issues = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="issues.list_for_repo",
            )
            raise  # Always raises, but needed for type checker

        else:
            return closed_issues

    async def get_open_pulls(self) -> list[PullRequestSimple]:
        """
        Get all open pulls.

        Returns
        -------
        list[PullRequestSimple]
            The list of open pulls.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIRequestError
            If the API request fails.
        """
        try:
            response: Response[
                list[PullRequestSimple]
            ] = await self.github.rest.pulls.async_list(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                state="open",
            )

            open_pulls = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="pulls.list",
            )
            raise  # Always raises, but needed for type checker

        else:
            return open_pulls

    async def get_closed_pulls(self) -> list[PullRequestSimple]:
        """
        Get all closed pulls.

        Returns
        -------
        list[PullRequestSimple]
            The list of closed pulls.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIRequestError
            If the API request fails.
        """
        try:
            response: Response[
                list[PullRequestSimple]
            ] = await self.github.rest.pulls.async_list(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                state="closed",
            )

            closed_pulls = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="pulls.list",
            )
            raise  # Always raises, but needed for type checker

        else:
            return closed_pulls

    async def get_pull(self, pr_number: int) -> PullRequest:
        """
        Get a pull request.

        Parameters
        ----------
        pr_number : int
            The number of the pull request.

        Returns
        -------
        PullRequest
            The pull request.

        Raises
        ------
        TuxAPIConnectionError
            If connection to GitHub API fails.
        TuxAPIRequestError
            If the API request fails.
        TuxAPIResourceNotFoundError
            If the pull request is not found.
        """
        try:
            response: Response[PullRequest] = await self.github.rest.pulls.async_get(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                pr_number,
            )

            pull = response.parsed_data

        except Exception as e:
            convert_httpx_error(
                e,
                service_name="GitHub",
                endpoint="pulls.get",
                not_found_resource=f"Pull Request #{pr_number}",
            )
            raise  # Always raises, but needed for type checker

        else:
            return pull
