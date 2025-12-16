"""
Toggle snippet lock commands.

This module provides functionality for locking and unlocking
code snippets to prevent or allow modifications.
"""

import contextlib

import discord
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission

from . import SnippetsBaseCog


class ToggleSnippetLock(SnippetsBaseCog):
    """Discord cog for toggling snippet locks."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the toggle snippet lock cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.command(
        name="togglesnippetlock",
        aliases=["tsl"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def toggle_snippet_lock(self, ctx: commands.Context[Tux], name: str) -> None:
        """Toggle the lock status of a snippet.

        Only users with moderator permissions can use this command.
        Locked snippets cannot be edited or deleted by regular users.
        Attempts to DM the snippet author about the status change.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        name : str
            The name of the snippet to lock or unlock.
        """
        assert ctx.guild

        # Fetch the snippet, send error if not found
        snippet = await self._get_snippet_or_error(ctx, name)
        if not snippet:
            return

        # Toggle the lock status in the database
        try:
            snippet_id = self._require_snippet_id(snippet)
        except ValueError:
            await self.send_snippet_error(ctx, description="Snippet ID is invalid.")
            return

        try:
            status = await self.db.snippet.toggle_snippet_lock_by_id(snippet_id)
        except Exception as e:
            logger.error(
                f"Failed to toggle lock for snippet '{name}' (ID: {snippet_id}): {e}",
            )
            await self.send_snippet_error(
                ctx,
                description="An error occurred while trying to toggle the snippet lock. Please try again later.",
            )
            return

        if status is None:
            logger.error(
                f"Toggle lock for snippet '{name}' (ID: {snippet_id}) succeeded but returned None status.",
            )
            await self.send_snippet_error(
                ctx,
                description="An unexpected issue occurred while toggling the snippet lock.",
            )
            return

        # Confirmation and logging
        lock_status_text = "locked" if status.locked else "unlocked"
        await ctx.send(
            f"Snippet `{name}` has been {lock_status_text}.",
            ephemeral=True,
        )
        logger.info(f"{ctx.author} {lock_status_text} snippet '{name}'.")

        # Attempt to notify the author via DM
        if author := self.bot.get_user(snippet.snippet_user_id):
            dm_message = (
                f"Your snippet `{snippet.snippet_name}` in server `{ctx.guild.name}` has been {lock_status_text}.\n\n"
                f"**What does this mean?**\n"
                f"If a snippet is locked, it cannot be edited or deleted by anyone other than moderators (like you perhaps!). "
                f"If unlocked, the original author can modify it again.\n\n"
                f"**Why?**\n"
                f"Snippets might be locked/unlocked by moderators for various reasons, often related to server utility or content stability. "
                f"If you believe this was done in error, please contact the server staff."
            )
            with contextlib.suppress(
                discord.Forbidden,
                discord.HTTPException,
            ):  # Catch potential DM errors
                await author.send(dm_message)
                logger.debug(
                    f"Sent lock status DM to snippet author {author} for snippet '{name}'.",
                )


async def setup(bot: Tux) -> None:
    """Load the ToggleSnippetLock cog."""
    await bot.add_cog(ToggleSnippetLock(bot))
