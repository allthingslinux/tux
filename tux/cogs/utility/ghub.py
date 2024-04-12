import os

import discord
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
        )
        embed.add_field(name="Issue Title", value=sel_issue.title)
        embed.add_field(name="URL", value=sel_issue.url)

    @group_issues.command(name="add", description="Add an issue to GitHub.")
    async def add(
        self,
        interaction: discord.Interaction,
        title: str,
        repo: str = "allthingslinux/tux",
    ) -> None:
        repo = g.get_repo(repo)
        new_issue = repo.create_issue(title=title)
        embed = EmbedCreator.create_success_embed(
            title="Issue Created!",
            description="Issue #: " + str(new_issue.number) + " | Repo: " + repo.full_name,
        )  # type: ignore
        embed.add_field(name="Issue Title", value=new_issue.title)
        embed.add_field(name="URL", value=new_issue.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Gthub(bot))
