# import discord
# import github
# from discord import app_commands
# from discord.ext import commands
# from github import Auth, Github
# from loguru import logger

# from tux.utils.constants import Constants as CONST
# from tux.utils.embeds import EmbedCreator

# auth = Auth.Token(CONST.GITHUB_TOKEN)
# g = Github(auth=auth)


# class GitHub(commands.Cog):
#     def __init__(self, bot: commands.Bot):
#         self.bot = bot

#     group_issues = app_commands.Group(name="issues", description="Mess with GitHub Issues.")
#     group_pr = app_commands.Group(name="pr", description="Mess with GitHub Pull Requests.")

#     @commands.has_any_role("Contributor", "Owner", "Admin")
#     @group_issues.command(name="get", description="Get a certain github issue.")
#     async def grab(
#         self, interaction: discord.Interaction, issue: int, repo: str = CONST.GITHUB_REPO
#     ) -> None:
#         try:
#             repository = g.get_repo(repo)
#             sel_issue = repository.get_issue(number=issue)

#             embed = EmbedCreator.create_success_embed(
#                 title="Issue Information",
#                 description=f"Issue #: {issue} | Repo: {repository.full_name}",
#                 interaction=interaction,
#             )
#             embed.add_field(name="Issue Title", value=sel_issue.title)
#             embed.add_field(name="URL", value=sel_issue.url)

#         except github.UnknownObjectException:
#             logger.error(
#                 f"{interaction.user} failed to use the get command in {interaction.channel}."
#             )
#             embed = EmbedCreator.create_error_embed(
#                 title="Error",
#                 description="Issue not found. Please check the issue number and repository name.",
#             )

#         logger.info(f"{interaction.user} used the get command in {interaction.channel}.")
#         await interaction.response.send_message(embed=embed)

#     @commands.has_any_role("Contributor", "Owner", "Admin")
#     @group_issues.command(name="add", description="Add an issue to GitHub.")
#     async def add(
#         self,
#         interaction: discord.Interaction,
#         title: str,
#         repo: str = CONST.GITHUB_REPO,
#     ) -> None:
#         # Doing some basic concept of an error handler to ensure that a fake repo isn't put in. it HAS handling, it just
#         # doesn't look very pretty, so I smashed it into an embed.
#         try:
#             repository = g.get_repo(repo)

#             new_issue = repository.create_issue(title=title)

#             embed = EmbedCreator.create_success_embed(
#                 title="Issue Created!",
#                 description=f"Issue #: {new_issue.number!s} | Repo: {repository.full_name}",
#                 interaction=interaction,
#             )
#             embed.add_field(name="Issue Title", value=new_issue.title)
#             embed.add_field(name="URL", value=new_issue.url)

#         except github.UnknownObjectException:
#             logger.error(
#                 f"{interaction.user} failed to use the add command in {interaction.channel}."
#             )
#             embed = EmbedCreator.create_error_embed(
#                 title="Error", description="Repo or issue not found.", interaction=interaction
#             )

#         logger.info(f"{interaction.user} used the add command in {interaction.channel}.")
#         await interaction.response.send_message(embed=embed)

#     @commands.has_any_role("Contributor", "Owner", "Admin")
#     @group_issues.command(name="comment", description="comment on  an issue on GitHub.")
#     async def cmt(
#         self,
#         interaction: discord.Interaction,
#         comment: str,
#         issue: int,
#         repo: str = CONST.GITHUB_REPO,
#     ) -> None:
#         try:
#             repository = g.get_repo(repo)
#             sel_issue = repository.get_issue(number=issue)
#             sel_issue.create_comment(comment)

#             embed = EmbedCreator.create_success_embed(
#                 title="Comment Created!",
#                 description=f"Issue #: {sel_issue.number!s} | Repo: {repository.full_name}",
#                 interaction=interaction,
#             )
#             embed.add_field(name="Comment", value=comment)
#             embed.add_field(name="URL", value=sel_issue.url)

#         except github.UnknownObjectException:
#             logger.error(
#                 f"{interaction.user} failed to use the comment command in {interaction.channel}."
#             )
#             embed = EmbedCreator.create_error_embed(
#                 title="Error", description="Repo or issue not found.", interaction=interaction
#             )

#         logger.info(f"{interaction.user} used the comment command in {interaction.channel}.")
#         await interaction.response.send_message(embed=embed)

#     # Pull request stuff starts here. make sure your socks are on tight.
#     @commands.has_any_role("Contributor", "Owner", "Admin")
#     @group_pr.command(name="create", description="Create a pull request.")
#     async def create(
#         self,
#         interaction: discord.Interaction,
#         base: str,
#         compare: str,
#         title: str,
#         body: str,
#         repo: str = CONST.GITHUB_REPO,
#     ) -> None:
#         try:
#             repository = g.get_repo(repo)
#             body += " This pull request was sent via Tux."
#             pr = repository.create_pull(base=base, head=compare, title=title, body=body)

#             embed = EmbedCreator.create_success_embed(
#                 title="Pull Request Created!",
#                 description=f"Number: {pr.number!s}| Repo:{repository.full_name}",
#                 interaction=interaction,
#             )
#             embed.add_field(name="Base", value=base)
#             embed.add_field(name="Compare", value=compare)
#             embed.add_field(name="Url", value=pr.url)
#             embed.add_field(name="PR Title", value=pr.title)

#         except github.UnknownObjectException:
#             embed = EmbedCreator.create_error_embed(
#                 title="Error",
#                 description="Repo or pull request not found.",
#                 interaction=interaction,
#             )
#             logger.error(
#                 f"{interaction.user} failed to use the create command in {interaction.channel}."
#             )

#         # Something is telling me the formatting above isn't correct, but that can be sorted out on pull request.

#         logger.info(f"{interaction.user} used the add command in {interaction.channel}.")
#         await interaction.response.send_message(embed=embed)

#     @commands.has_any_role("Contributor", "Owner", "Admin")
#     @group_pr.command(name="get", description="Get a certain github P.R.")
#     async def get(
#         self,
#         interaction: discord.Interaction,
#         pr: int,
#         repo: str = CONST.GITHUB_REPO,
#     ) -> None:
#         try:
#             repository = g.get_repo(repo)
#             sel_pr = repository.get_pull(number=pr)

#             embed = EmbedCreator.create_success_embed(
#                 title="Issue Information",
#                 description=f"Issue #: {pr} | Repo: {repository.full_name}",
#                 interaction=interaction,
#             )
#             embed.add_field(name="PR Title", value=sel_pr.title)
#             embed.add_field(name="URL", value=sel_pr.url)
#             embed.add_field(name="Base", value=sel_pr.base)
#             embed.add_field(name="Compare", value=sel_pr.head)

#         except github.UnknownObjectException:
#             logger.error(
#                 f"{interaction.user} failed to use the get command in {interaction.channel}."
#             )
#             embed = EmbedCreator.create_error_embed(
#                 title="Error",
#                 description="Repo or pull request not found.",
#                 interaction=interaction,
#             )
#             logger.error(
#                 f"{interaction.user} failed to use the create command in {interaction.channel}."
#             )

#         logger.info(f"{interaction.user} used the get command in {interaction.channel}.")
#         await interaction.response.send_message(embed=embed)

#     @commands.has_any_role("Contributor", "Owner", "Admin")
#     @group_pr.command(name="comment", description="comment on  a pull request on GitHub.")
#     async def comment(
#         self,
#         interaction: discord.Interaction,
#         comment: str,
#         pr: int,
#         repo: str = CONST.GITHUB_REPO,
#     ) -> None:
#         try:
#             repository = g.get_repo(repo)
#             sel_pr = repository.get_pull(number=pr)
#             sel_pr.create_issue_comment(comment)

#             embed = EmbedCreator.create_success_embed(
#                 title="Comment Created!",
#                 description=f"PR #: {sel_pr.number!s} | Repo: {repository.full_name}",
#                 interaction=interaction,
#             )
#             embed.add_field(name="Comment", value=comment)
#             embed.add_field(name="URL", value=sel_pr.url)

#         except github.UnknownObjectException:
#             logger.error(
#                 f"{interaction.user} failed to use the comment command in {interaction.channel}."
#             )
#             embed = EmbedCreator.create_error_embed(
#                 title="Error",
#                 description="Repo or pull request not found.",
#                 interaction=interaction,
#             )

#         logger.info(f"{interaction.user} used the cmt command in {interaction.channel}.")
#         await interaction.response.send_message(embed=embed)


# async def setup(bot: commands.Bot) -> None:
#     await bot.add_cog(GitHub(bot))

import discord
import github
from discord import app_commands
from discord.ext import commands
from github import Auth, Github
from loguru import logger

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator

auth = Auth.Token(CONST.GITHUB_TOKEN)
g = Github(auth=auth)


class GitHub(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group_issues = app_commands.Group(name="issues", description="Mess with GitHub Issues.")
    group_pr = app_commands.Group(name="pr", description="Mess with GitHub Pull Requests.")

    async def _get_repo(self, interaction: discord.Interaction, repo: str):
        try:
            return g.get_repo(repo)
        except github.UnknownObjectException:
            logger.error(f"{interaction.user} failed to get repository {repo} in {interaction.channel}.")
            return None

    async def _get_issue(self, interaction: discord.Interaction, repo: str, issue: int):
        repository = await self._get_repo(interaction, repo)
        if repository is None:
            return None

        try:
            return repository.get_issue(number=issue)
        except github.UnknownObjectException:
            logger.error(f"{interaction.user} failed to get issue #{issue} in {interaction.channel}.")
            return None

    async def _create_error_embed(self, title, description, interaction) -> discord.Embed:
        return EmbedCreator.create_error_embed(title=title, description=description, interaction=interaction)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_issues.command(name="get", description="Get a certain github issue.")
    async def grab(self, interaction: discord.Interaction, issue: int, repo: str = CONST.GITHUB_REPO) -> None:
        issue = await self._get_issue(interaction, repo, issue)
        if issue is None:
            embed = await self._create_error_embed("Error", "Issue not found. Please check the issue number and repository name.", interaction)
        else:
            embed = EmbedCreator.create_success_embed(title="Issue Information", description=f"Issue #: {issue} | Repo: {repository.full_name}", interaction=interaction)
            embed.add_field(name="Issue Title", value=issue.title)
            embed.add_field(name="URL", value=issue.url)

        logger.info(f"{interaction.user} used the get command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_issues.command(name="add", description="Add an issue to GitHub.")
    async def add(self,interaction: discord.Interaction,title: str,repo: str = CONST.GITHUB_REPO,) -> None:
        repository = await self._get_repo(interaction, repo)
        if repository is None: return

        new_issue = repository.create_issue(title=title)

        embed = EmbedCreator.create_success_embed(title="Issue Created!", description=f"Issue #: {new_issue.number!s} | Repo: {repository.full_name}", interaction=interaction)
        embed.add_field(name="Issue Title", value=new_issue.title)
        embed.add_field(name="URL", value=new_issue.url)

        logger.info(f"{interaction.user} used the add command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_issues.command(name="comment", description="Comment on an issue on GitHub.")
    async def cmt(self,interaction: discord.Interaction,comment: str,issue: int,repo: str = CONST.GITHUB_REPO,) -> None:
        issue = await self._get_issue(interaction, repo, issue)
        if issue is None:
            embed = await self._create_error_embed("Error", "Issue not found. Please check the issue number and repository name.", interaction)
        else:
            issue.create_comment(comment)
            embed = EmbedCreator.create_success_embed(title="Comment Created!", description=f"Issue #: {issue.number!s} | Repo: {repository.full_name}", interaction=interaction)
            embed.add_field(name="Comment", value=comment)
            embed.add_field(name="URL", value=issue.url)

        logger.info(f"{interaction.user} used the comment command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_pr.command(name="create", description="Create a pull request.")
    async def create(self,interaction: discord.Interaction,base: str,compare: str,title: str,body: str,repo: str = CONST.GITHUB_REPO,) -> None:
        repository = await self._get_repo(interaction, repo)
        if repository is None:
            embed = await self._create_error_embed("Error", "Repo not found.", interaction)
        else:
            body += " This pull request was sent via Tux."
            pr = repository.create_pull(base=base, head=compare, title=title, body=body)
            embed = EmbedCreator.create_success_embed(title="Pull Request Created!", description=f"Number: {pr.number!s}| Repo:{repository.full_name}", interaction=interaction)
            embed.add_field(name="Base", value=base)
            embed.add_field(name="Compare", value=compare)
            embed.add_field(name="Url", value=pr.url)
            embed.add_field(name="PR Title", value=pr.title)

        logger.info(f"{interaction.user} used the add command in {interaction.channel}.")
        await interaction.response.send_message(embed=embed)

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_pr.command(name="get", description="Get a certain github P.R.")
    async def get(self,interaction: discord.Interaction,pr: int,repo: str = CONST.GITHUB_REPO,) -> None:
        .....

    @commands.has_any_role("Contributor", "Owner", "Admin")
    @group_pr.command(name="comment", description="Comment on a pull request on GitHub.")
    async def comment(self,interaction: discord.Interaction,comment: str,pr: int,repo: str = CONST.GITHUB_REPO,) -> None:
        .....

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GitHub(bot))