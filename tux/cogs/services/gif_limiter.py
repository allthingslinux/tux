import asyncio
from collections import defaultdict
from time import time
from typing import defaultdict

from tux.utils.constants import Constants as CONST
from tux.bot import Tux

import discord
from discord.ext import commands, tasks
from loguru import logger

from tux.bot import Tux
from tux.utils.constants import CONST


# Helper function required as YAML keys are str. Channel and user IDs are int.
def convert_dict_str_to_int(original_dict: dict[str, int]) -> dict[int, int]:
    converted_dict: dict[int, int] = {}

    for key, value in original_dict.items():
        try:
            int_key: int = int(key)
            converted_dict[int_key] = value
        except ValueError:
            logger.error("An error occurred when loading the GIF ratelimiter configuration.")

    return converted_dict


class GifLimiter(commands.Cog):
    """
    This class is a handler for GIF ratelimiting.
    It keeps a list of GIF send times and routinely removes old times.
    If a user posts a GIF, the message_handler function should be externally called.
    It will delete the message if the user, channel or server-wide quota is exceeded.
    """

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        # Read config options and save them to local variables to avoid excessive reads
        # From the CONST[] dictionary
        self.recent_gif_age: int = CONST.RECENT_GIF_AGE  # Max age for a GIF to be considered a recent post
        self.channelwide_gif_limits: dict[int, int] = convert_dict_str_to_int(
            CONST.GIF_LIMITS_CHANNEL
        )  # Max GIFs sent recently for specific channels
        self.user_gif_limits: dict[int, int] = convert_dict_str_to_int(
            CONST.GIF_LIMITS
        )  # Max recent GIFs sent by a user to be able to send a GIF in a channel
        self.gif_limit_exclude: list[int] = CONST.GIF_LIMIT_EXCLUDE  # list of channels in which not to count GIFs

        # Timestamps for recently-sent GIFs for the server, and channels
        self.recent_gifs_by_user: defaultdict[int, list[int]] = defaultdict(list)  # UID, list of timestamps
        self.recent_gifs_by_channel: defaultdict[int, list[int]] = defaultdict(list)  # Channel ID, list of timestamps
        self.recent_gifs_serverwide: list[int] = []

    # Deletes the message passed as an argument, and creates a self-deleting message explaining the reason
    async def delete_message(self, message: discord.Message, epilogue: str) -> None:
        channel: Union[TextChannel, StageChannel, VoiceChannel, Thread, DMChannel, GroupChannel, PartialMessageable]
        = message.channel

        await message.delete()
        sent_message: discord.Message = await channel.send("-# GIF ratelimit exceeded " + epilogue)
        await asyncio.sleep(3)
        await sent_message.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Nothing to do if the message doesn't have a .gif embed, or if it was sent in a blacklisted channel
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

    # Function regularly cleans GIF lists and only keeps the most recent ones
    @tasks.loop(seconds=20)
    async def old_gif_remover(self) -> None:
        current_time: int = int(time())

        for channel_id, timestamps in self.recent_gifs_by_channel.items():
            self.recent_gifs_by_channel[channel_id] = [t for t in timestamps if current_time - t < self.recent_gif_age]

        for user_id, timestamps in self.recent_gifs_by_user.items():
            self.recent_gifs_by_user[user_id] = [t for t in timestamps if current_time - t < self.recent_gif_age]

            # Delete user key if no GIF has recently been sent by them
            if len(self.recent_gifs_by_user[user_id]) == 0:
                del self.recent_gifs_by_user[user_id]


async def setup(bot: Tux) -> None:
    await bot.add_cog(GifLimiter(bot))
