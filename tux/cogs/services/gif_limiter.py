import asyncio
from collections import defaultdict
from time import time

import discord
from discord.ext import commands, tasks

from tux.bot import Tux
from tux.utils.constants import CONST


class GifLimiter(commands.Cog):
    """
    This class is a handler for GIF ratelimiting.
    It keeps a list of GIF send times and routinely removes old times.
    It will prevent people from posting GIFs if the quotas are exceeded.
    """

    def __init__(self, bot: Tux) -> None:
        self.bot = bot

        # Max age for a GIF to be considered a recent post
        self.recent_gif_age: int = CONST.RECENT_GIF_AGE

        # Max number of GIFs sent recently in a channel
        self.channelwide_gif_limits: dict[int, int] = CONST.GIF_LIMITS_CHANNEL
        # Max number of GIFs sent recently by a user to be able to post one in specified channels
        self.user_gif_limits: dict[int, int] = CONST.GIF_LIMITS

        # list of channels in which not to count GIFs
        self.gif_limit_exclude: list[int] = CONST.GIF_LIMIT_EXCLUDE

        # Timestamps for recently-sent GIFs for the server, and channels

        # UID, list of timestamps
        self.recent_gifs_by_user: defaultdict[int, list[int]] = defaultdict(list)
        # Channel ID, list of timestamps
        self.recent_gifs_by_channel: defaultdict[int, list[int]] = defaultdict(list)

        # Lock to prevent race conditions
        self.gif_lock = asyncio.Lock()

        self.old_gif_remover.start()

    async def _should_process_message(self, message: discord.Message) -> bool:
        """Checks if a message contains a GIF and was not sent in a blacklisted channel"""
        return not (
            len(message.embeds) == 0
            or "gif" not in message.content.lower()
            or message.channel.id in self.gif_limit_exclude
        )

    async def _handle_gif_message(self, message: discord.Message) -> None:
        """Checks for ratelimit infringements"""
        async with self.gif_lock:
            channel: int = message.channel.id
            user: int = message.author.id

            if (
                channel in self.channelwide_gif_limits
                and len(self.recent_gifs_by_channel[channel]) >= self.channelwide_gif_limits[channel]
            ):
                await self._delete_message(message, "for channel")
                return

            if channel in self.user_gif_limits and len(self.recent_gifs_by_user[user]) >= self.user_gif_limits[channel]:
                await self._delete_message(message, "for user")
                return

            # Add message to recent GIFs if it doesn't infringe on ratelimits
            current_time: int = int(time())
            self.recent_gifs_by_channel[channel].append(current_time)
            self.recent_gifs_by_user[user].append(current_time)

    async def _delete_message(self, message: discord.Message, epilogue: str) -> None:
        """
        Deletes the message passed as an argument, and sends a self-deleting message with the reason
        """
        await message.delete()
        await message.channel.send(f"-# GIF ratelimit exceeded {epilogue}", delete_after=3)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Checks for GIFs in every sent message"""

        if await self._should_process_message(message):
            await self._handle_gif_message(message)

    @tasks.loop(seconds=20)
    async def old_gif_remover(self) -> None:
        """Regularly cleans old GIF timestamps"""
        current_time: int = int(time())

        async with self.gif_lock:
            for channel_id, timestamps in list(self.recent_gifs_by_channel.items()):
                self.recent_gifs_by_channel[channel_id] = [
                    t for t in timestamps if current_time - t < self.recent_gif_age
                ]

            for user_id, timestamps in list(self.recent_gifs_by_user.items()):
                filtered_timestamps = [t for t in timestamps if current_time - t < self.recent_gif_age]
                if filtered_timestamps:
                    self.recent_gifs_by_user[user_id] = filtered_timestamps
                else:
                    del self.recent_gifs_by_user[user_id]


async def setup(bot: Tux) -> None:
    await bot.add_cog(GifLimiter(bot))
