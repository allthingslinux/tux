"""
Edit snippet commands.

This module provides functionality for editing existing code snippets
in Discord guilds with ownership and permission validation.
"""

from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux

from . import SnippetsBaseCog


class EditSnippet(SnippetsBaseCog):
    """Discord cog for editing snippets."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the edit snippet cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.command(
        name="editsnippet",
        aliases=["es"],
    )
    @commands.guild_only()
    async def edit_snippet(
        self,
        ctx: commands.Context[Tux],
        name: str,
        *,
        content: str,
    ) -> None:
        """Edit an existing snippet.

        Checks for ownership and lock status before editing.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        name : str
            The name of the snippet to edit.
        content : str
            The new content for the snippet.
        """
        assert ctx.guild

        # Fetch the snippet, send error if not found
        snippet = await self._get_snippet_or_error(ctx, name)

        if not snippet:
            return

        # Check permissions (role, ban, lock, ownership)
        can_edit, reason = await self.snippet_check(
            ctx,
            snippet_locked=snippet.locked,
            snippet_user_id=snippet.snippet_user_id,
        )

        if not can_edit:
            await self.send_snippet_error(ctx, description=reason)
            return

        # Update the snippet content
        try:
            snippet_id = self._require_snippet_id(snippet)
            await self.db.snippet.update_snippet_by_id(
                snippet_id=snippet_id,
                snippet_content=content,
            )
        except ValueError:
            await self.send_snippet_error(ctx, description="Snippet ID is invalid.")
            return

        await ctx.send("Snippet edited.", ephemeral=True)

        logger.info(f"{ctx.author} edited snippet '{name}'. Override: {reason}")


async def setup(bot: Tux) -> None:
    """Load the EditSnippet cog."""
    await bot.add_cog(EditSnippet(bot))
