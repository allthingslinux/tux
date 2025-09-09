"""
Communication service for moderation operations.

Handles DM sending, embed creation, and user communication without
the complexity of mixin inheritance.
"""

import contextlib
from datetime import datetime
from typing import cast

import discord
from discord.ext import commands

from tux.core.types import Tux
from tux.shared.constants import CONST


class CommunicationService:
    """
    Service for handling moderation-related communication.

    Manages DM sending, embed creation, and user notifications
    with proper error handling and timeouts.
    """

    def __init__(self, bot: Tux):
        """
        Initialize the communication service.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot

    async def send_dm(
        self,
        ctx: commands.Context[Tux],
        silent: bool,
        user: discord.Member | discord.User,
        reason: str,
        dm_action: str,
    ) -> bool:
        """
        Send a DM to a user about a moderation action.

        Args:
            ctx: Command context
            silent: Whether to send DM (if False, returns False immediately)
            user: Target user
            reason: Reason for the action
            dm_action: Action description for DM

        Returns:
            True if DM was sent successfully, False otherwise
        """
        if silent:
            return False

        try:
            # Get the user object, handling both User and Member types
            author: discord.User | discord.Member = ctx.author
            author_user = author if isinstance(author, discord.User) else author.user  # type: ignore[attr-defined]
            embed = self._create_dm_embed(dm_action, reason, cast(discord.User, author_user))
            await user.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException, AttributeError, TimeoutError):
            return False
        else:
            return True

    async def send_error_response(
        self,
        ctx: commands.Context[Tux] | discord.Interaction,
        message: str,
        ephemeral: bool = True,
    ) -> None:
        """
        Send an error response to the user.

        Args:
            ctx: Command context
            message: Error message to send
            ephemeral: Whether the response should be ephemeral
        """
        try:
            if isinstance(ctx, discord.Interaction):
                if ctx.response.is_done():
                    await ctx.followup.send(message, ephemeral=ephemeral)
                else:
                    await ctx.response.send_message(message, ephemeral=ephemeral)
            else:
                # ctx is commands.Context[Tux] here
                await ctx.reply(message, mention_author=False)
        except discord.HTTPException:
            # If sending fails, try to send without reply
            with contextlib.suppress(discord.HTTPException):
                if isinstance(ctx, discord.Interaction):
                    # For interactions, use followup
                    await ctx.followup.send(message, ephemeral=ephemeral)
                else:
                    # For command contexts, use send
                    await ctx.send(message)

    def create_embed(
        self,
        ctx: commands.Context[Tux],
        title: str,
        fields: list[tuple[str, str, bool]],
        color: int,
        icon_url: str,
        timestamp: datetime | None = None,
        thumbnail_url: str | None = None,
    ) -> discord.Embed:
        """
        Create a moderation embed.

        Args:
            ctx: Command context
            title: Embed title
            fields: List of (name, value, inline) tuples
            color: Embed color
            icon_url: Icon URL for the embed
            timestamp: Optional timestamp
            thumbnail_url: Optional thumbnail URL

        Returns:
            The created embed
        """
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=timestamp or discord.utils.utcnow(),
        )

        embed.set_author(name=ctx.author.name, icon_url=icon_url)

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.display_avatar.url,
        )

        return embed

    async def send_embed(
        self,
        ctx: commands.Context[Tux],
        embed: discord.Embed,
        log_type: str = "mod",
    ) -> discord.Message | None:
        """
        Send an embed and optionally log it.

        Args:
            ctx: Command context
            embed: The embed to send
            log_type: Type of log entry

        Returns:
            The sent message if successful
        """
        try:
            # Send the embed as a regular message
            message = await ctx.send(embed=embed, mention_author=False)

            # Also send as ephemeral followup for slash commands
            if isinstance(ctx, discord.Interaction):
                embed_ephemeral = embed.copy()
                embed_ephemeral.set_footer(text="This is only visible to you")
                await ctx.followup.send(embed=embed_ephemeral, ephemeral=True)

        except discord.HTTPException:
            await self.send_error_response(ctx, "Failed to send embed")
            return None
        else:
            return message

    def _create_dm_embed(
        self,
        action: str,
        reason: str,
        moderator: discord.User,
    ) -> discord.Embed:
        """
        Create a DM embed for moderation actions.

        Args:
            action: The action that was taken
            reason: Reason for the action
            moderator: The moderator who performed the action

        Returns:
            The DM embed
        """
        embed = discord.Embed(
            title=f"You have been {action}",
            color=CONST.EMBED_COLORS["CASE"],
            timestamp=discord.utils.utcnow(),
        )

        embed.add_field(
            name="Reason",
            value=reason or "No reason provided",
            inline=False,
        )

        embed.add_field(
            name="Moderator",
            value=f"{moderator} ({moderator.id})",
            inline=False,
        )

        embed.set_footer(
            text="If you believe this was an error, please contact server staff",
        )

        return embed
