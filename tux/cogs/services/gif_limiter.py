"""
This cog is a handler for GIF ratelimiting.
It keeps a list of GIF send times and routinely removes old times.
If a user posts a GIF, the message_handler function should be externally called.
It will delete the message if the user or channel quota is exceeded.
"""

import asyncio
from collections import defaultdict
from time import time

import discord
from discord import Message
from discord.ext import commands, tasks
from loguru import logger

from tux.bot import Tux
from tux.utils.constants import CONST


def convert_dict_str_to_int(original_dict: dict[str, int]) -> dict[int, int]:
    """Helper function required as YAML keys are str. Channel and user IDs are int."""

    converted_dict: dict[int, int] = {}

    for key, value in original_dict.items():
        try:
            int_key: int = int(key)
            converted_dict[int_key] = value
        except ValueError:
            logger.error("An error occurred when loading the GIF ratelimiter configuration.")

    return converted_dict


class GifLimiter(commands.Cog):
    """Main class with GIF tracking and message handlers"""

    def __init__(self, bot: Tux) -> None:
        self.bot = bot

        # Max age for a GIF to be considered a recent post
        self.recent_gif_age: int = CONST.RECENT_GIF_AGE

        # Max number of GIFs sent recently in a channel
        self.channelwide_gif_limits: dict[int, int] = convert_dict_str_to_int(CONST.GIF_LIMITS_CHANNEL)
        # Max number of GIFs sent recently by a user to be able to post one in specified channels
        self.user_gif_limits: dict[int, int] = convert_dict_str_to_int(CONST.GIF_LIMITS)

        # list of channels in which not to count GIFs
        self.gif_limit_exclude: list[int] = CONST.GIF_LIMIT_EXCLUDE

        # Timestamps for recently-sent GIFs for the server, and channels

        # UID, list of timestamps
        self.recent_gifs_by_user: defaultdict[int, list[int]] = defaultdict(list)
        # Channel ID, list of timestamps
        self.recent_gifs_by_channel: defaultdict[int, list[int]] = defaultdict(list)

    async def delete_message(self, message: discord.Message, epilogue: str) -> None:
        """
        Deletes the message passed as an argument, and sends a self-deleting message with the reason
        """
        sent_message: Message = await message.channel.send(f"-# GIF ratelimit exceeded {epilogue}")
        await message.delete()
        await asyncio.sleep(3)
        await sent_message.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Checks for GIFs in every sent message"""

        # Nothing to do if the message doesn't have a .gif embed,
        # or if it was sent in a blacklisted channel
        if (
            len(message.embeds) == 0
            or "gif" not in message.content.lower()
            or message.channel.id in self.gif_limit_exclude
        ):
            return

        channel: int = message.channel.id
        user: int = message.author.id

        # Check if the message infringes on any ratelimits
        if (
            channel in self.channelwide_gif_limits
            and channel in self.recent_gifs_by_channel
            and len(self.recent_gifs_by_channel[channel]) >= self.channelwide_gif_limits[channel]
        ):
            await self.delete_message(message, "for channel")
            return

        if (
            user in self.recent_gifs_by_user
            and channel in self.user_gif_limits
            and len(self.recent_gifs_by_user[user]) >= self.user_gif_limits[channel]
        ):
            await self.delete_message(message, "for user")
            return

        # If it doesn't, add it to recent GIFs
        current_time: int = int(time())
        self.recent_gifs_by_channel[channel].append(current_time)
        self.recent_gifs_by_user[user].append(current_time)

    @tasks.loop(seconds=20)
    async def old_gif_remover(self) -> None:
        """Regularly cleans old GIF timestamps"""
        current_time: int = int(time())

        for channel_id, timestamps in self.recent_gifs_by_channel.items():
            self.recent_gifs_by_channel[channel_id] = (
                [t for t in timestamps if current_time - t < self.recent_gif_age])

        for user_id, timestamps in self.recent_gifs_by_user.items():
            self.recent_gifs_by_user[user_id] = (
                [t for t in timestamps if current_time - t < self.recent_gif_age])

            # Delete user key if no GIF has recently been sent by them
            if len(self.recent_gifs_by_user[user_id]) == 0:
                del self.recent_gifs_by_user[user_id]


async def setup(bot: Tux) -> None:
    await bot.add_cog(GifLimiter(bot))
