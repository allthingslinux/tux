import discord
from bot import Tux
from database.controllers import DatabaseController
from discord.ext import commands
from loguru import logger
from ui.embeds import EmbedCreator, EmbedType
from utils import checks
from utils.config import Config
from utils.constants import CONST

from prisma.enums import CaseType
from prisma.models import Snippet


class SnippetsBaseCog(commands.Cog):
    """Base class for Snippet Cogs, providing shared utilities."""

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()

    async def is_snippetbanned(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is currently snippet banned in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is snippet banned, False otherwise.
        """
        return await self.db.case.is_user_under_restriction(
            guild_id=guild_id,
            user_id=user_id,
            active_restriction_type=CaseType.SNIPPETBAN,
            inactive_restriction_type=CaseType.SNIPPETUNBAN,
        )

    def _create_snippets_list_embed(
        self,
        ctx: commands.Context[Tux],
        snippets: list[Snippet],
        total_snippets: int,
        search_query: str | None = None,
    ) -> discord.Embed:
        """Create an embed for displaying a paginated list of snippets.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        snippets : list[Snippet]
            The list of snippets for the current page.
        total_snippets : int
            The total number of snippets matching the query.
        search_query : str | None
            The search query used, if any.

        Returns
        -------
        discord.Embed
            The generated embed.
        """
        assert ctx.guild
        assert ctx.guild.icon

        if not snippets:
            return EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedType.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                description="No snippets found.",
            )

        description = "\n".join(
            f"`{'🔒' if snippet.locked else ' '}{'→' if snippet.alias else ' '}{i + 1}`. {snippet.snippet_name} (`{snippet.uses}` uses)"
            for i, snippet in enumerate(snippets)
        )
        count = len(snippets)
        total_snippets = total_snippets or 0
        embed_title = f"Snippets ({count}/{total_snippets})"

        footer_text, footer_icon_url = EmbedCreator.get_footer(
            bot=ctx.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        return EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title=embed_title,
            description=description or "No snippets found.",
            custom_author_text=ctx.guild.name,
            custom_author_icon_url=ctx.guild.icon.url,
            message_timestamp=ctx.message.created_at,
            custom_footer_text=footer_text,
            custom_footer_icon_url=footer_icon_url,
        )

    async def check_if_user_has_mod_override(self, ctx: commands.Context[Tux]) -> bool:
        """Check if the user invoking the command has moderator permissions (PL >= configured level)."""
        try:
            await checks.has_pl(2).predicate(ctx)
        except commands.CheckFailure:
            return False
        except Exception as e:
            logger.error(f"Unexpected error in check_if_user_has_mod_override: {e}")
            return False
        else:
            return True

    async def snippet_check(
        self,
        ctx: commands.Context[Tux],
        snippet_locked: bool = False,
        snippet_user_id: int = 0,
    ) -> tuple[bool, str]:
        """Check if a user is allowed to modify or delete a snippet.

        Checks for moderator override, snippet bans, role restrictions,
        snippet lock status, and snippet ownership.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        snippet_locked : bool, optional
            Whether the snippet is locked. Checked only if True. Defaults to False.
        snippet_user_id : int, optional
            The ID of the snippet's author. Checked only if non-zero. Defaults to 0.

        Returns
        -------
        tuple[bool, str]
            A tuple containing a boolean indicating permission status and a reason string.
        """
        assert ctx.guild

        if await self.check_if_user_has_mod_override(ctx):
            return True, "Mod override granted."

        if await self.is_snippetbanned(ctx.guild.id, ctx.author.id):
            return False, "You are banned from using snippets."

        if (
            Config.LIMIT_TO_ROLE_IDS
            and isinstance(ctx.author, discord.Member)
            and all(role.id not in Config.ACCESS_ROLE_IDS for role in ctx.author.roles)
        ):
            roles_str = ", ".join([f"<@&{role_id}>" for role_id in Config.ACCESS_ROLE_IDS])
            return (
                False,
                f"You do not have a role that allows you to manage snippets. Accepted roles: {roles_str}",
            )

        if snippet_locked:
            return False, "This snippet is locked. You cannot edit or delete it."

        # Allow if snippet_user_id is 0 (not provided, e.g., for create) or matches the author.
        if snippet_user_id not in (0, ctx.author.id):
            return False, "You can only edit or delete your own snippets."

        return True, "All checks passed."

    async def _get_snippet_or_error(self, ctx: commands.Context[Tux], name: str) -> Snippet | None:
        """Fetch a snippet by name and guild, sending an error embed if not found.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet to fetch.

        Returns
        -------
        Snippet | None
            The fetched Snippet object, or None if not found.
        """
        assert ctx.guild
        snippet = await self.db.snippet.get_snippet_by_name_and_guild_id(name, ctx.guild.id)
        if snippet is None:
            await self.send_snippet_error(ctx, description="Snippet not found.")
            return None
        return snippet

    async def send_snippet_error(self, ctx: commands.Context[Tux], description: str) -> None:
        """Send a standardized snippet error embed.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        description : str
            The error message description.
        """
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.ERROR,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            description=description,
        )
        await ctx.send(embed=embed, delete_after=CONST.DEFAULT_DELETE_AFTER)
