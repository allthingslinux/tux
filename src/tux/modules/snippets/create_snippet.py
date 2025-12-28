"""
Create snippet commands.

This module provides functionality for creating new code snippets
and aliases in Discord guilds with validation and permission checking.
"""

import re

from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.shared.constants import SNIPPET_ALLOWED_CHARS_REGEX, SNIPPET_MAX_NAME_LENGTH

from . import SnippetsBaseCog


class CreateSnippet(SnippetsBaseCog):
    """Discord cog for creating snippets and aliases."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the create snippet cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.command(
        name="createsnippet",
        aliases=["cs"],
    )
    @commands.guild_only()
    async def create_snippet(
        self,
        ctx: commands.Context[Tux],
        name: str,
        *,
        content: str,
    ) -> None:
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

        author_id = ctx.author.id
        guild_id = ctx.guild.id

        # Check if a snippet with this name already exists
        try:
            existing_snippet = await self.db.snippet.get_snippet_by_name_and_guild_id(
                name,
                guild_id,
            )
            if existing_snippet is not None:
                await self.send_snippet_error(
                    ctx,
                    description="Snippet with this name already exists.",
                )
                return
        except Exception as e:
            logger.error(f"Failed to check existing snippet: {e}")
            await self.send_snippet_error(ctx, description="Database error occurred.")
            return

        # Validate snippet name format and length
        if len(name) > SNIPPET_MAX_NAME_LENGTH or not re.match(
            SNIPPET_ALLOWED_CHARS_REGEX,
            name,
        ):
            await self.send_snippet_error(
                ctx,
                description=f"Snippet name must be alphanumeric (allows dashes only) and less than {SNIPPET_MAX_NAME_LENGTH} characters.",
            )
            return

        # Check if content matches another snippet name to automatically create an alias
        try:
            existing_snippet_for_alias = (
                await self.db.snippet.get_snippet_by_name_and_guild_id(
                    content,
                    guild_id,
                )
            )

            if existing_snippet_for_alias:
                await self.db.snippet.create_snippet_alias(
                    original_name=content,
                    alias_name=name,
                    guild_id=guild_id,
                )

                await ctx.send(
                    f"Snippet `{name}` created as an alias pointing to `{content}`.",
                    ephemeral=True,
                )

                logger.info(
                    f"{ctx.author} created snippet '{name}' as an alias to '{content}'.",
                )
                return

            # Create the new snippet
            await self.db.snippet.create_snippet(
                snippet_name=name,
                snippet_content=content,
                snippet_user_id=author_id,
                guild_id=guild_id,
            )

            await ctx.send("Snippet created.", ephemeral=True)
            logger.success(f"{ctx.author} created snippet '{name}'.")

        except Exception as e:
            logger.error(f"Failed to create snippet: {e}")
            await self.send_snippet_error(ctx, description="Failed to create snippet.")
            return


async def setup(bot: Tux) -> None:
    """Set up the CreateSnippet cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(CreateSnippet(bot))
