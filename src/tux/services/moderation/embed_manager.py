"""
Embed management for moderation actions.

Handles creation and sending of moderation embeds and log messages.
"""

import logging
from datetime import datetime

import discord
from discord.ext import commands

from tux.core.types import Tux
from tux.ui.embeds import EmbedCreator, EmbedType

logger = logging.getLogger(__name__)


class EmbedManager:
    """
    Manages embed creation and sending for moderation actions.

    This mixin provides functionality to:
    - Create standardized moderation embeds
    - Send embeds to log channels
    - Send error response embeds
    - Format case titles and descriptions
    """

    async def send_error_response(
        self,
        ctx: commands.Context[Tux],
        error_message: str,
        error_detail: Exception | None = None,
        ephemeral: bool = True,
    ) -> None:
        """
        Send a standardized error response.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        error_message : str
            The error message to display.
        error_detail : Optional[Exception]
            The exception details, if available.
        ephemeral : bool
            Whether the message should be ephemeral.
        """
        if error_detail:
            logging.error(f"{error_message}: {error_detail}")

        embed = EmbedCreator.create_embed(
            bot=getattr(self, "bot", None),
            embed_type=EmbedCreator.ERROR,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            description=error_message,
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

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
        Create an embed for moderation actions.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        title : str
            The title of the embed.
        fields : list[tuple[str, str, bool]]
            The fields to add to the embed.
        color : int
            The color of the embed.
        icon_url : str
            The icon URL for the embed.
        timestamp : Optional[datetime]
            The timestamp for the embed.
        thumbnail_url : Optional[str]
            The thumbnail URL for the embed.

        Returns
        -------
        discord.Embed
            The embed for the moderation action.
        """

        footer_text, footer_icon_url = EmbedCreator.get_footer(
            bot=getattr(self, "bot", None),
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=title,
            custom_color=color,
            message_timestamp=timestamp or ctx.message.created_at,
            custom_author_icon_url=icon_url,
            thumbnail_url=thumbnail_url,
            custom_footer_text=footer_text,
            custom_footer_icon_url=footer_icon_url,
        )

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        return embed

    async def send_embed(
        self,
        ctx: commands.Context[Tux],
        embed: discord.Embed,
        log_type: str,
    ) -> discord.Message | None:
        """
        Send an embed to the log channel and return the message.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        embed : discord.Embed
            The embed to send.
        log_type : str
            The type of log to send the embed to.

        Returns
        -------
        discord.Message | None
            The sent message, or None if sending failed.
        """

        assert ctx.guild

        db = getattr(self, "db", None)
        if not db:
            return None

        log_channel_id = await db.guild_config.get_log_channel(ctx.guild.id, log_type)

        if log_channel_id:
            log_channel = ctx.guild.get_channel(log_channel_id)

            if isinstance(log_channel, discord.TextChannel):
                try:
                    return await log_channel.send(embed=embed)
                except discord.HTTPException as e:
                    logger.warning(f"Failed to send embed to log channel: {e}")
                    return None

        return None
