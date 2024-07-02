import discord
from discord import app_commands
from discord.ext import commands
from githubkit.versions.latest.models import (
    Issue,
)
from loguru import logger

from tux.services.github import GitHubService
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class LinkButton(discord.ui.View):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="View on Github",
                url=url,
            )
        )


class Git(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.git = GitHubService()
        self.repo_url = CONST.GITHUB_REPO_URL

    group = app_commands.Group(name="git", description="Github commands.")

    async def create_error_embed(self, interaction: discord.Interaction, error: str) -> None:
        """
        Create an error embed and send it as a followup message for all commands.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation
        error : str
            The error message to display.
        """

        embed = EmbedCreator.create_error_embed(
            title="Uh oh!",
            description=error,
            interaction=interaction,
        )

        await interaction.followup.send(embed=embed)

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="get_repo", description="Get repository information.")
    async def get_repo(self, interaction: discord.Interaction) -> None:
        """
        Get repository information.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        """

        await interaction.response.defer()

        try:
            repo = await self.git.get_repo()

            embed = EmbedCreator.create_info_embed(
                title="Tux",
                description="",
                interaction=interaction,
            )
            embed.add_field(name="Description", value=repo.description, inline=False)
            embed.add_field(name="Stars", value=repo.stargazers_count)
            embed.add_field(name="Forks", value=repo.forks_count)
            embed.add_field(name="Open Issues", value=repo.open_issues_count)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error fetching repository: {e}")
            logger.error(f"Error fetching repository: {e}")

        else:
            await interaction.followup.send(embed=embed, view=LinkButton(repo.html_url))
            logger.info(f"{interaction.user} fetched repository information.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="create_issue", description="Create an issue.")
    async def create_issue(
        self,
        interaction: discord.Interaction,
        title: str,
        body: str,
    ) -> None:
        """
        Create an issue.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        title : str
            The title of the issue.
        body : str
            The body of the issue.
        """

        await interaction.response.defer()

        try:
            created_issue = await self.git.create_issue(title, body)

            embed = EmbedCreator.create_success_embed(
                title="Issue Created",
                description="The issue has been created successfully.",
                interaction=interaction,
            )
            embed.add_field(name="Issue Number", value=created_issue.number, inline=False)
            embed.add_field(name="Title", value=title)
            embed.add_field(name="Body", value=body)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error creating issue: {e}")
            logger.error(f"Error creating issue: {e}")

        else:
            await interaction.followup.send(embed=embed, view=LinkButton(created_issue.html_url))
            logger.info(f"{interaction.user} created an issue.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="create_issue_comment", description="Create an issue comment.")
    async def create_issue_comment(
        self,
        interaction: discord.Interaction,
        issue_number: int,
        body: str,
    ) -> None:
        """
        Create an issue comment.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        issue_number : int
            The number of the issue to comment on.
        body : str
            The body of the comment.
        """

        await interaction.response.defer()

        try:
            created_issue_comment = await self.git.create_issue_comment(issue_number, body)

            embed = EmbedCreator.create_success_embed(
                title="Comment Created",
                description="The comment has been created successfully.",
                interaction=interaction,
            )
            embed.add_field(name="Issue Number", value=issue_number, inline=False)
            embed.add_field(name="Body", value=body, inline=False)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error creating comment: {e}")
            logger.error(f"Error creating comment: {e}")

        else:
            await interaction.followup.send(embed=embed, view=LinkButton(created_issue_comment.html_url))
            logger.info(f"{interaction.user} created a comment.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="close_issue", description="Close an issue.")
    async def close_issue(
        self,
        interaction: discord.Interaction,
        issue_number: int,
    ) -> None:
        """
        Close an issue.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        issue_number : int
            The number of the issue to close.
        """

        await interaction.response.defer()

        try:
            closed_issue = await self.git.close_issue(issue_number)

            embed = EmbedCreator.create_success_embed(
                title="Issue Closed",
                description="The issue has been closed successfully.",
                interaction=interaction,
            )
            embed.add_field(name="Issue Number", value=issue_number)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error closing issue: {e}")
            logger.error(f"Error closing issue: {e}")

        else:
            await interaction.followup.send(embed=embed, view=LinkButton(closed_issue.html_url))
            logger.info(f"{interaction.user} closed an issue.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="get_issue", description="Get an issue.")
    async def get_issue(
        self,
        interaction: discord.Interaction,
        issue_number: int,
    ) -> None:
        """
        Get an issue.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        issue_number : int
            The number of the issue to retrieve.
        """

        await interaction.response.defer()

        try:
            issue = await self.git.get_issue(issue_number)

            embed = EmbedCreator.create_info_embed(
                title=issue.title,
                description=str(issue.body) if issue.body is not None else "",
                interaction=interaction,
            )
            embed.add_field(name="State", value=issue.state)
            embed.add_field(name="Number", value=issue.number)
            embed.add_field(name="User", value=issue.user.login if issue.user else "Unknown")
            embed.add_field(name="Created At", value=issue.created_at)
            embed.add_field(name="Updated At", value=issue.updated_at)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error fetching issue: {e}")
            logger.error(f"Error fetching issue: {e}")

        else:
            await interaction.followup.send(embed=embed, view=LinkButton(issue.html_url))
            logger.info(f"{interaction.user} fetched an issue.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="get_open_issues", description="Get open issues.")
    async def get_open_issues(self, interaction: discord.Interaction) -> None:
        """
        Get open issues.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        """

        await interaction.response.defer()

        try:
            open_issues: list[Issue] = await self.git.get_open_issues()

            embed = EmbedCreator.create_info_embed(
                title="Open Issues",
                description="Here are the open issues for the repository.",
                interaction=interaction,
            )

            for issue in open_issues[:25]:
                embed.add_field(name=issue.title, value=str(issue.number), inline=False)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error fetching issues: {e}")
            logger.error(f"Error fetching issues: {e}")

        else:
            await interaction.followup.send(
                embed=embed,
                view=LinkButton(f"{self.repo_url}/issues?q=is%3Aissue+is%3Aopen"),
            )
            logger.info(f"{interaction.user} fetched open issues.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="get_closed_issues", description="Get closed issues.")
    async def get_closed_issues(self, interaction: discord.Interaction) -> None:
        """
        Get closed issues.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        """

        await interaction.response.defer()

        try:
            closed_issues = await self.git.get_closed_issues()

            embed = EmbedCreator.create_info_embed(
                title="Closed Issues",
                description="Here are the closed issues for the repository.",
                interaction=interaction,
            )

            for issue in closed_issues[:25]:
                embed.add_field(name=issue.title, value=str(issue.number), inline=False)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error fetching issues: {e}")
            logger.error(f"Error fetching issues: {e}")

        else:
            await interaction.followup.send(
                embed=embed,
                view=LinkButton("https://github.com/allthingslinux/tux/issues?q=is%3Aissue+is%3Aclosed"),
            )
            logger.info(f"{interaction.user} fetched closed issues.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="get_open_pulls", description="Get open pull requests.")
    async def get_open_pulls(self, interaction: discord.Interaction) -> None:
        """
        Get open pull requests.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        """

        await interaction.response.defer()

        try:
            open_pulls = await self.git.get_open_pulls()

            embed = EmbedCreator.create_info_embed(
                title="Open Pull Requests",
                description="Here are the open pull requests for the repository.",
                interaction=interaction,
            )

            for pull in open_pulls[:25]:
                embed.add_field(name=pull.title, value=str(pull.number), inline=False)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error fetching pull requests: {e}")
            logger.error(f"Error fetching pull requests: {e}")

        else:
            await interaction.followup.send(
                embed=embed,
                view=LinkButton("https://github.com/allthingslinux/tux/pulls?q=is%3Aopen+is%3Apr"),
            )
            logger.info(f"{interaction.user} fetched open pull requests.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="get_closed_pulls", description="Get closed pull requests.")
    async def get_closed_pulls(self, interaction: discord.Interaction) -> None:
        """
        Get closed pull requests.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        """

        await interaction.response.defer()

        try:
            closed_pulls = await self.git.get_closed_pulls()

            embed = EmbedCreator.create_info_embed(
                title="Closed Pull Requests",
                description="Here are the closed pull requests for the repository.",
                interaction=interaction,
            )

            for pull in closed_pulls[:25]:
                embed.add_field(name=pull.title, value=str(pull.number), inline=False)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error fetching pull requests: {e}")
            logger.error(f"Error fetching pull requests: {e}")

        else:
            await interaction.followup.send(
                embed=embed,
                view=LinkButton("https://github.com/allthingslinux/tux/"),
            )
            logger.info(f"{interaction.user} fetched closed pull requests.")

    @app_commands.checks.has_any_role("Contributor", "Root", "Admin")
    @group.command(name="get_pull", description="Get a pull request.")
    async def get_pull(
        self,
        interaction: discord.Interaction,
        pull_number: int,
    ) -> None:
        """
        Get a pull request.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the command invocation.
        pull_number : int
            The number of the pull request to retrieve.
        """

        await interaction.response.defer()

        try:
            pull = await self.git.get_pull(pull_number)

            embed = EmbedCreator.create_info_embed(
                title=pull.title,
                description=str(pull.body) if pull.body is not None else "",
                interaction=interaction,
            )
            embed.add_field(name="State", value=pull.state)
            embed.add_field(name="Number", value=pull.number)
            embed.add_field(name="User", value=pull.user.login)
            embed.add_field(name="Created At", value=pull.created_at)
            embed.add_field(name="Updated At", value=pull.updated_at)

        except Exception as e:
            await self.create_error_embed(interaction, f"Error fetching pull request: {e}")
            logger.error(f"Error fetching pull request: {e}")

        else:
            await interaction.followup.send(embed=embed, view=LinkButton(pull.html_url))
            logger.info(f"{interaction.user} fetched a pull request.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Git(bot))
