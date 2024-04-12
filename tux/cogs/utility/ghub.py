import os

import discord
import github
from discord import app_commands
from discord.ext import commands
from github import Auth, Github

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
    async def get(
        self,
        interaction: discord.Interaction,
        issue: int,
        repo: str = "allthingslinux/tux",
    ) -> None:
        repo = g.get_repo(repo)
        sel_issue = repo.get_issue(number=issue)
        embed = EmbedCreator.create_success_embed(
            title="Issue Information",
            description="Issue #: " + str(issue) + " | Repo: " + repo.full_name,
            interaction=interaction,
        )
        embed.add_field(name="Issue Title", value=sel_issue.title)
        embed.add_field(name="URL", value=sel_issue.url)
        await interaction.response.send_message(embed=embed)

    @group_issues.command(name="add", description="Add an issue to GitHub.")
    async def add(
        self,
        interaction: discord.Interaction,
        title: str,
        repo: str = "allthingslinux/tux",
    ) -> None:
        try:
            repo2 = g.get_repo(repo)
        except github.UnknownObjectException:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Repo not found.", interaction=interaction
            )
            await interaction.response.send_message(embed=embed)
        new_issue = repo2.create_issue(title=title)
        embed = EmbedCreator.create_success_embed(
            title="Issue Created!",
            description="Issue #: " + str(new_issue.number) + " | Repo: " + repo2.full_name,
            interaction=interaction,
        )  # type: ignore
        embed.add_field(name="Issue Title", value=new_issue.title)
        embed.add_field(name="URL", value=new_issue.url)
        await interaction.response.send_message(embed=embed)

    @group_issues.command(name="comment", description="comment on  an issue on GitHub.")
    async def comment(
        self,
        interaction: discord.Interaction,
        comment: str,
        issue: int,
        repo: str = "allthingslinux/tux",
    ) -> None:
        try:
            used_repo = g.get_repo(repo)
        except github.UnknownObjectException:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Repo not found.", interaction=interaction
            )
            await interaction.response.send_message(embed=embed)
        sel_issue = used_repo.get_issue(number=issue)
        sel_issue.create_comment(comment)
        embed = EmbedCreator.create_success_embed(
            title="Comment Created!",
            description="Issue #: " + str(sel_issue.number) + " | Repo: " + used_repo.full_name,
            interaction=interaction,
        )  # type: ignore
        embed.add_field(name="Comment", value=comment)
        embed.add_field(name="URL", value=sel_issue.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Gthub(bot))
