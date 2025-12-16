"""
Delete snippet commands.

This module provides functionality for deleting existing code snippets
from Discord guilds with ownership and permission validation.
"""

from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux

from . import SnippetsBaseCog


class DeleteSnippet(SnippetsBaseCog):
    """Discord cog for deleting snippets."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the delete snippet cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.command(
        name="deletesnippet",
        aliases=["ds"],
    )
    @commands.guild_only()
    async def delete_snippet(self, ctx: commands.Context[Tux], name: str) -> None:
        """Delete a snippet by name.

        Checks for ownership and lock status before deleting.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        name : str
            The name of the snippet to delete.
        """
        assert ctx.guild

        # Fetch the snippet, send error if not found
        snippet = await self._get_snippet_or_error(ctx, name)
        if not snippet:
            return

        # Check permissions (role, ban, lock, ownership)
        can_delete, reason = await self.snippet_check(
            ctx,
            snippet_locked=snippet.locked,
            snippet_user_id=snippet.snippet_user_id,
        )

        if not can_delete:
            await self.send_snippet_error(ctx, description=reason)
            return

        # Delete the snippet
        try:
            snippet_id = self._require_snippet_id(snippet)
            await self.db.snippet.delete_snippet_by_id(snippet_id)
        except ValueError:
            await self.send_snippet_error(ctx, description="Snippet ID is invalid.")
            return

        await ctx.send("Snippet deleted.", ephemeral=True)

        logger.info(f"{ctx.author} deleted snippet '{name}'. Override: {reason}")


async def setup(bot: Tux) -> None:
    """Load the DeleteSnippet cog."""
    await bot.add_cog(DeleteSnippet(bot))
