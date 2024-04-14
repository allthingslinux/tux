import os

import discord
import github
from discord import app_commands
from discord.ext import commands
from github import Auth, Github
from loguru import logger

from tux.utils.embeds import EmbedCreator

auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
g = Github(auth=auth)


class Gthub(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group_issues = app_commands.Group(name="issues", description="Mess with github Issues.")
    group_pr = app_commands.Group(name="pr", description="Mess with GitHub Pull Requests.")

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_issues.command(name="get", description="Get a certain github issue.")
    async def grab(
        self,
        interaction: discord.Interaction,
        issue: int,
        repo: str = "allthingslinux/tux",
    ) -> None:
        try:
            repo = g.get_repo(repo)
            sel_issue = repo.get_issue(number=issue)
        except github.UnknownObjectException:
            logger.error(
                f"{interaction.user} failed to use the get command in {interaction.channel}."
            )
            await interaction.response.send_message(
                embed=EmbedCreator.create_error_embed(
                    title="Error",
                    description="Issue not found. Please check the issue number and repository name.",
                )
            )
        embed = EmbedCreator.create_success_embed(
            title="Issue Information",
            description="Issue #: " + str(issue) + " | Repo: " + repo.full_name,
            interaction=interaction,
        )
        embed.add_field(name="Issue Title", value=sel_issue.title)
        embed.add_field(name="URL", value=sel_issue.url)
        logger.info(f"{interaction.user} used the get command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_issues.command(name="add", description="Add an issue to GitHub.")
    async def add(
        self,
        interaction: discord.Interaction,
        title: str,
        repo: str = "allthingslinux/tux",
    ) -> None:
        # Doing some basic concept of an error handler to ensure that a fake repo isn't put in. it HAS handling, it just
        # doesn't look very pretty, so I smashed it into an embed.
        try:
            repo2 = g.get_repo(repo)
        except github.UnknownObjectException:
            logger.error(
                f"{interaction.user} failed to use the add command in {interaction.channel}."
            )
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Repo or issue not found.", interaction=interaction
            )
            await interaction.response.send_message(embed=embed)
        new_issue = repo2.create_issue(title=title)
        embed = EmbedCreator.create_success_embed(
            title="Issue Created!",
            description="Issue #: " + str(new_issue.number) + " | Repo: " + repo2.full_name,
            interaction=interaction,
        )  # type: ignore
        logger.info(f"{interaction.user} used the add command in {interaction.channel}.")
        embed.add_field(name="Issue Title", value=new_issue.title)
        embed.add_field(name="URL", value=new_issue.url)
        await interaction.response.send_message(embed=embed)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_issues.command(name="comment", description="comment on  an issue on GitHub.")
    async def cmt(
        self,
        interaction: discord.Interaction,
        comment: str,
        issue: int,
        repo: str = "allthingslinux/tux",
    ) -> None:
        try:
            used_repo = g.get_repo(repo)
        except github.UnknownObjectException:
            logger.error(
                f"{interaction.user} failed to use the comment command in {interaction.channel}."
            )
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Repo or issue not found.", interaction=interaction
            )
            await interaction.response.send_message(embed=embed)
        sel_issue = used_repo.get_issue(number=issue)
        sel_issue.create_comment(comment)
        embed = EmbedCreator.create_success_embed(
            title="Comment Created!",
            description="Issue #: " + str(sel_issue.number) + " | Repo: " + used_repo.full_name,
            interaction=interaction,
        )  # type: ignore
        logger.info(f"{interaction.user} used the comment command in {interaction.channel}.")
        embed.add_field(name="Comment", value=comment)
        embed.add_field(name="URL", value=sel_issue.url)
        await interaction.response.send_message(embed=embed)

    # Pull request stuff starts here. make sure your socks are on tight.
    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_pr.command(name="create", description="Create a pull request.")
    async def create(
        self,
        interaction: discord.Interaction,
        base: str,
        compare: str,
        title: str,
        body: str,
        repo: str = "allthingslinux/tux",
    ) -> None:
        try:
            target_repo = g.get_repo(repo)
        except github.UnknownObjectException:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Repo or pull request not found.",
                interaction=interaction,
            )
            logger.error(
                f"{interaction.user} failed to use the create command in {interaction.channel}."
            )
            await interaction.response.send_message(embed=embed)
        body = body + " This pull request was sent via Tux."
        pr = target_repo.create_pull(base=base, head=compare, title=title, body=body)
        embed = EmbedCreator.create_success_embed(
            title="Pull Request Created!",
            description="Number: " + str(pr.number) + "| Repo:" + target_repo.full_name,
            interaction=interaction,
        )
        # Something is telling me the formatting above isn't correct, but that can be sorted out on pull request.

        embed.add_field(name="Base", value=base)
        embed.add_field(name="Compare", value=compare)
        embed.add_field(name="Url", value=pr.url)
        embed.add_field(name="PR Title", value=pr.title)
        logger.info(f"{interaction.user} used the add command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_pr.command(name="get", description="Get a certain github P.R.")
    async def get(
        self,
        interaction: discord.Interaction,
        pr: int,
        repo: str = "allthingslinux/tux",
    ) -> None:
        try:
            repo = g.get_repo(repo)
            sel_pr = repo.get_pull(number=pr)
        except github.UnknownObjectException:
            logger.error(
                f"{interaction.user} failed to use the get command in {interaction.channel}."
            )
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Repo or pull request not found.",
                interaction=interaction,
            )
            logger.error(
                f"{interaction.user} failed to use the create command in {interaction.channel}."
            )
            await interaction.response.send_message(embed=embed)

        embed = EmbedCreator.create_success_embed(
            title="Issue Information",
            description="Issue #: " + str(pr) + " | Repo: " + repo.full_name,
            interaction=interaction,
        )
        embed.add_field(name="PR Title", value=sel_pr.title)
        embed.add_field(name="URL", value=sel_pr.url)
        embed.add_field(name="Base", value=sel_pr.base)
        embed.add_field(name="Compare", value=sel_pr.head)
        logger.info(f"{interaction.user} used the get command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_pr.command(name="comment", description="comment on  a pull request on GitHub.")
    async def comment(
        self,
        interaction: discord.Interaction,
        comment: str,
        pr: int,
        repo: str = "allthingslinux/tux",
    ) -> None:
        try:
            used_repo = g.get_repo(repo)
        except github.UnknownObjectException:
            logger.error(
                f"{interaction.user} failed to use the comment command in {interaction.channel}."
            )
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Repo or pull request not found.",
                interaction=interaction,
            )
            await interaction.response.send_message(embed=embed)
        sel_pr = used_repo.get_pull(number=pr)
        sel_pr.create_comment(comment)
        embed = EmbedCreator.create_success_embed(
            title="Comment Created!",
            description="PR #: " + str(sel_pr.number) + " | Repo: " + used_repo.full_name,
            interaction=interaction,
        )  # type: ignore
        embed.add_field(name="Comment", value=comment)
        embed.add_field(name="URL", value=sel_pr.url)
        logger.info(f"{interaction.user} used the cmt command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Gthub(bot))
