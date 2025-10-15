import httpx
from githubkit import AppInstallationAuthStrategy, GitHub, Response
from githubkit.versions.latest.models import (
    FullRepository,
    Issue,
    IssueComment,
    PullRequest,
    PullRequestSimple,
)
from loguru import logger

from tux.shared.config import CONFIG
from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIPermissionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
)


class GithubService:
    def __init__(self) -> None:
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
        """
        try:
            response: Response[FullRepository] = await self.github.rest.repos.async_get(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
            )

            repo: FullRepository = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching repository: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == 404:
                    raise TuxAPIResourceNotFoundError(
                        service_name="GitHub",
                        resource_identifier=f"{CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER}/{CONFIG.EXTERNAL_SERVICES.GITHUB_REPO}",
                    ) from e
                if e.response.status_code == 403:
                    raise TuxAPIPermissionError(service_name="GitHub") from e
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise  # Re-raise other unexpected exceptions

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
            logger.error(f"Error creating issue: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == 403:
                    raise TuxAPIPermissionError(service_name="GitHub") from e
                # Add more specific error handling if needed, e.g., 422 for validation
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

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
        """
        try:
            response: Response[IssueComment] = await self.github.rest.issues.async_create_comment(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                issue_number,
                body=body,
            )

            created_issue_comment = response.parsed_data

        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == 403:
                    raise TuxAPIPermissionError(service_name="GitHub") from e
                if e.response.status_code == 404:  # Issue not found
                    raise TuxAPIResourceNotFoundError(
                        service_name="GitHub",
                        resource_identifier=f"Issue #{issue_number}",
                    ) from e
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

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
            logger.error(f"Error closing issue: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == 404:  # Issue not found
                    raise TuxAPIResourceNotFoundError(
                        service_name="GitHub",
                        resource_identifier=f"Issue #{issue_number}",
                    ) from e
                if e.response.status_code == 403:
                    raise TuxAPIPermissionError(service_name="GitHub") from e
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

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
        """
        try:
            response: Response[Issue] = await self.github.rest.issues.async_get(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                issue_number,
            )

            issue = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching issue: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == 404:
                    raise TuxAPIResourceNotFoundError(
                        service_name="GitHub",
                        resource_identifier=f"Issue #{issue_number}",
                    ) from e
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

        else:
            return issue

    async def get_open_issues(self) -> list[Issue]:
        """
        Get all open issues.

        Returns
        -------
        list[Issue]
            The list of open issues.
        """
        try:
            response: Response[list[Issue]] = await self.github.rest.issues.async_list_for_repo(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                state="open",
            )

            open_issues = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

        else:
            return open_issues

    async def get_closed_issues(self) -> list[Issue]:
        """
        Get all closed issues.

        Returns
        -------
        list[Issue]
            The list of closed issues.
        """
        try:
            response: Response[list[Issue]] = await self.github.rest.issues.async_list_for_repo(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                state="closed",
            )

            closed_issues = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

        else:
            return closed_issues

    async def get_open_pulls(self) -> list[PullRequestSimple]:
        """
        Get all open pulls.

        Returns
        -------
        list[PullRequestSimple]
            The list of open pulls.
        """
        try:
            response: Response[list[PullRequestSimple]] = await self.github.rest.pulls.async_list(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                state="open",
            )

            open_pulls = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching PRs: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

        else:
            return open_pulls

    async def get_closed_pulls(self) -> list[PullRequestSimple]:
        """
        Get all closed pulls.

        Returns
        -------
        list[PullRequestSimple]
            The list of closed pulls.
        """
        try:
            response: Response[list[PullRequestSimple]] = await self.github.rest.pulls.async_list(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                state="closed",
            )

            closed_pulls = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching PRs: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

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
        """
        try:
            response: Response[PullRequest] = await self.github.rest.pulls.async_get(
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO_OWNER,
                CONFIG.EXTERNAL_SERVICES.GITHUB_REPO,
                pr_number,
            )

            pull = response.parsed_data

        except Exception as e:
            logger.error(f"Error fetching PR: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == 404:
                    raise TuxAPIResourceNotFoundError(
                        service_name="GitHub",
                        resource_identifier=f"Pull Request #{pr_number}",
                    ) from e
                raise TuxAPIRequestError(
                    service_name="GitHub",
                    status_code=e.response.status_code,
                    reason=e.response.text,
                ) from e
            if isinstance(e, httpx.RequestError):
                raise TuxAPIConnectionError(service_name="GitHub", original_error=e) from e
            raise

        else:
            return pull
