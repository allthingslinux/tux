"""
GIF rate limiting service for Discord channels.

This module provides automatic rate limiting for GIF attachments and links
in Discord channels to prevent spam and maintain conversation quality.
"""

import asyncio
from collections import defaultdict
from time import time

import discord
from discord.ext import commands, tasks

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.config import CONFIG


class GifLimiter(BaseCog):
    """
    Handler for GIF ratelimiting.

    This class keeps a list of GIF send times and routinely removes old times.
    It will prevent people from posting GIFs if the quotas are exceeded.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the GIF limiter service.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this service to.
        """
        super().__init__(bot)

        # Max age for a GIF to be considered a recent post
        self.recent_gif_age: int = CONFIG.GIF_LIMITER.RECENT_GIF_AGE

        # Max number of GIFs sent recently in a channel
        self.channelwide_gif_limits: dict[int, int] = (
            CONFIG.GIF_LIMITER.GIF_LIMITS_CHANNEL
        )
        # Max number of GIFs sent recently by a user to be able to post one in specified channels
        self.user_gif_limits: dict[int, int] = CONFIG.GIF_LIMITER.GIF_LIMITS_USER

        # list of channels in which not to count GIFs
        self.gif_limit_exclude: list[int] = CONFIG.GIF_LIMITER.GIF_LIMIT_EXCLUDE

        # Timestamps for recently-sent GIFs for the server, and channels

        # UID, list of timestamps
        self.recent_gifs_by_user: defaultdict[int, list[int]] = defaultdict(list)
        # Channel ID, list of timestamps
        self.recent_gifs_by_channel: defaultdict[int, list[int]] = defaultdict(list)

        # Lock to prevent race conditions
        self.gif_lock = asyncio.Lock()

        self.old_gif_remover.start()

    async def _should_process_message(self, message: discord.Message) -> bool:
        """
        Check if a message contains a GIF and was not sent in a blacklisted channel.

        Parameters
        ----------
        message : discord.Message
            The message to check.

        Returns
        -------
        bool
            True if the message contains a GIF and was not sent in a blacklisted channel, False otherwise.
        """
        return not (
            not message.embeds
            or "gif" not in message.content.lower()
            or message.channel.id in self.gif_limit_exclude
        )

    async def _handle_gif_message(self, message: discord.Message) -> None:
        """
        Check for ratelimit infringements.

        Parameters
        ----------
        message : discord.Message
            The message to check.
        """
        async with self.gif_lock:
            channel: int = message.channel.id
            user: int = message.author.id

            if (
                channel in self.channelwide_gif_limits
                and len(self.recent_gifs_by_channel[channel])
                >= self.channelwide_gif_limits[channel]
            ):
                await self._delete_message(message, "for channel")
                return

            if (
                channel in self.user_gif_limits
                and len(self.recent_gifs_by_user[user]) >= self.user_gif_limits[channel]
            ):
                await self._delete_message(message, "for user")
                return

            # Add message to recent GIFs if it doesn't infringe on ratelimits
            current_time: int = int(time())
            self.recent_gifs_by_channel[channel].append(current_time)
            self.recent_gifs_by_user[user].append(current_time)

    async def _delete_message(self, message: discord.Message, epilogue: str) -> None:
        """
        Delete the message passed as an argument, and sends a self-deleting message with the reason.

        Parameters
        ----------
        message : discord.Message
            The message to delete.
        epilogue : str
            The reason for the deletion.
        """
        await message.delete()
        await message.channel.send(
            f"-# GIF ratelimit exceeded {epilogue}",
            delete_after=3,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Check for GIFs in every sent message.

        Parameters
        ----------
        message : discord.Message
            The message to check.
        """
        if await self._should_process_message(message):
            await self._handle_gif_message(message)

    @tasks.loop(seconds=20, name="old_gif_remover")
    async def old_gif_remover(self) -> None:
        """
        Regularly clean old GIF timestamps.

        Parameters
        ----------
        self : GifLimiter
            The GifLimiter instance.
        """
        current_time: int = int(time())

        async with self.gif_lock:
            for channel_id, timestamps in list(self.recent_gifs_by_channel.items()):
                self.recent_gifs_by_channel[channel_id] = [
                    t for t in timestamps if current_time - t < self.recent_gif_age
                ]
            for user_id, timestamps in list(self.recent_gifs_by_user.items()):
                if filtered_timestamps := [
                    t for t in timestamps if current_time - t < self.recent_gif_age
                ]:
                    self.recent_gifs_by_user[user_id] = filtered_timestamps
                else:
                    del self.recent_gifs_by_user[user_id]

    @old_gif_remover.before_loop
    async def before_old_gif_remover(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()

    async def cog_unload(self) -> None:
        """Cancel the background task when the cog is unloaded."""
        self.old_gif_remover.cancel()


async def setup(bot: Tux) -> None:
    """Set up the GifLimiter cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(GifLimiter(bot))
