import re
from datetime import UTC, datetime

from bot import Tux
from discord.ext import commands
from loguru import logger
from utils.constants import CONST
from utils.functions import generate_usage

from . import SnippetsBaseCog


class CreateSnippet(SnippetsBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.create_snippet.usage = generate_usage(self.create_snippet)

    @commands.command(
        name="createsnippet",
        aliases=["cs"],
    )
    @commands.guild_only()
    async def create_snippet(self, ctx: commands.Context[Tux], name: str, *, content: str) -> None:
        """Create a new snippet or an alias.

        If the provided content exactly matches the name of an existing snippet,
        an alias pointing to that snippet will be created instead.

        Snippet names must be alphanumeric (allowing dashes) and under a configured length.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        name : str
            The desired name for the new snippet.
        content : str
            The content of the snippet, or the name of a snippet to alias.
        """
        assert ctx.guild

        # Check permissions (role, ban status)
        can_create, reason = await self.snippet_check(ctx)

        if not can_create:
            await self.send_snippet_error(ctx, description=reason)
            return

        created_at = datetime.now(UTC)
        author_id = ctx.author.id
        guild_id = ctx.guild.id

        # Check if a snippet with this name already exists
        if await self.db.snippet.get_snippet_by_name_and_guild_id(name, guild_id) is not None:
            await self.send_snippet_error(ctx, description="Snippet with this name already exists.")
            return

        # Validate snippet name format and length
        if len(name) > CONST.SNIPPET_MAX_NAME_LENGTH or not re.match(CONST.SNIPPET_ALLOWED_CHARS_REGEX, name):
            await self.send_snippet_error(
                ctx,
                description=f"Snippet name must be alphanumeric (allows dashes only) and less than {CONST.SNIPPET_MAX_NAME_LENGTH} characters.",
            )
            return

        # Check if content matches another snippet name to automatically create an alias
        existing_snippet_for_alias = await self.db.snippet.get_snippet_by_name_and_guild_id(
            content,
            guild_id,
        )

        if existing_snippet_for_alias:
            await self.db.snippet.create_snippet_alias(
                snippet_name=name,
                snippet_alias=content,
                snippet_created_at=created_at,
                snippet_user_id=author_id,
                guild_id=guild_id,
            )

            await ctx.send(
                f"Snippet `{name}` created as an alias pointing to `{content}`.",
                delete_after=CONST.DEFAULT_DELETE_AFTER,
                ephemeral=True,
            )

            logger.info(f"{ctx.author} created snippet '{name}' as an alias to '{content}'.")
            return

        # Create the new snippet
        await self.db.snippet.create_snippet(
            snippet_name=name,
            snippet_content=content,
            snippet_created_at=created_at,
            snippet_user_id=author_id,
            guild_id=guild_id,
        )

        await ctx.send("Snippet created.", delete_after=CONST.DEFAULT_DELETE_AFTER, ephemeral=True)

        logger.info(f"{ctx.author} created snippet '{name}'.")


async def setup(bot: Tux) -> None:
    await bot.add_cog(CreateSnippet(bot))
