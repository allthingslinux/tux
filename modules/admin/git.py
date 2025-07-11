from bot import Tux
from discord.ext import commands
from loguru import logger
from ui.buttons import GithubButton
from ui.embeds import EmbedCreator
from utils import checks
from utils.config import CONFIG
from utils.functions import generate_usage
from wrappers.github import GithubService


class Git(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.github = GithubService()
        self.repo_url = CONFIG.GITHUB_REPO_URL
        self.git.usage = generate_usage(self.git)
        self.get_repo.usage = generate_usage(self.get_repo)
        self.create_issue.usage = generate_usage(self.create_issue)
        self.get_issue.usage = generate_usage(self.get_issue)

    @commands.hybrid_group(
        name="git",
        aliases=["g"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def git(self, ctx: commands.Context[Tux]) -> None:
        """
        Github related commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send_help("git")

    @git.command(
        name="get_repo",
        aliases=["r"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def get_repo(self, ctx: commands.Context[Tux]) -> None:
        """
        Get repository information.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """

        try:
            repo = await self.github.get_repo()

            embed = EmbedCreator.create_embed(
                EmbedCreator.INFO,
                bot=self.bot,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Tux",
                description="",
            )
            embed.add_field(name="Description", value=repo.description, inline=False)
            embed.add_field(name="Stars", value=repo.stargazers_count)
            embed.add_field(name="Forks", value=repo.forks_count)
            embed.add_field(name="Open Issues", value=repo.open_issues_count)

        except Exception as e:
            await ctx.send(f"Error fetching repository: {e}", delete_after=30, ephemeral=True)
            logger.error(f"Error fetching repository: {e}")

        else:
            await ctx.send(embed=embed, view=GithubButton(repo.html_url))
            logger.info(f"{ctx.author} fetched repository information.")

    @git.command(
        name="create_issue",
        aliases=["ci"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def create_issue(self, ctx: commands.Context[Tux], title: str, body: str) -> None:
        """
        Create an issue.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        title : str
            The title of the issue.
        body : str
            The body of the issue.
        """

        try:
            issue_body = body + "\n\nAuthor: " + str(ctx.author)
            created_issue = await self.github.create_issue(title, issue_body)

            embed = EmbedCreator.create_embed(
                EmbedCreator.SUCCESS,
                bot=self.bot,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Issue Created",
                description="The issue has been created successfully.",
            )
            embed.add_field(name="Issue Number", value=created_issue.number, inline=False)
            embed.add_field(name="Title", value=title, inline=False)
            embed.add_field(name="Body", value=issue_body, inline=False)

        except Exception as e:
            await ctx.send(f"Error creating issue: {e}", delete_after=30, ephemeral=True)
            logger.error(f"Error creating issue: {e}")

        else:
            await ctx.send(embed=embed, view=GithubButton(created_issue.html_url))
            logger.info(f"{ctx.author} created an issue.")

    @git.command(
        name="get_issue",
        aliases=["gi", "issue", "i"],
    )
    @commands.guild_only()
    @checks.has_pl(8)
    async def get_issue(self, ctx: commands.Context[Tux], issue_number: int) -> None:
        """
        Get an issue by issue number.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        issue_number : int
            The number of the issue to retrieve.
        """

        try:
            issue = await self.github.get_issue(issue_number)

            embed = EmbedCreator.create_embed(
                EmbedCreator.INFO,
                bot=self.bot,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title=issue.title,
                description=str(issue.body) if issue.body is not None else "",
            )
            embed.add_field(name="State", value=issue.state, inline=False)
            embed.add_field(name="Number", value=issue.number, inline=False)
            embed.add_field(name="User", value=issue.user.login if issue.user else "Unknown", inline=False)
            embed.add_field(name="Created At", value=issue.created_at, inline=False)
            embed.add_field(name="Updated At", value=issue.updated_at, inline=False)

        except Exception as e:
            await ctx.send(f"Error fetching issue: {e}", delete_after=30, ephemeral=True)
            logger.error(f"Error fetching issue: {e}")

        else:
            await ctx.send(embed=embed, view=GithubButton(issue.html_url))
            logger.info(f"{ctx.author} fetched an issue.")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Git(bot))
