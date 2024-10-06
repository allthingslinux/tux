from collections import defaultdict

import discord
from discord.ext import commands, tasks
from loguru import logger

from tux.bot import Tux
from tux.utils.constants import CONST


class SlowmodeHandler(commands.Cog):
    """
    This class is an automatic slowmode handler.
    It counts each message, and every so often sets the slowmode for configured channels.
    """

    def __init__(self, bot: Tux) -> None:
        self.bot = bot

        # Channel ID, count
        self.message_counts: dict[int, int] = defaultdict(int)
        self.channel_converter = commands.TextChannelConverter()

        self.set_slowmode.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Adds messages to recent messages if the message channel is configured"""
        if message.channel.id in CONST.AUTOSLOWMODE_CHANNELS:
            self.message_counts[message.channel.id] += 1
            logger.info(f"current msgs for channel: {self.message_counts[message.channel.id]}")

    @tasks.loop(seconds=CONST.AUTOSLOWMODE_INTERVAL)
    async def set_slowmode(self) -> None:
        """Sets slowmode for configured channels according to the thresholds"""

        # dict() call to create a copy and avoid issues if the dictionary is modified while iterating
        for channel_id in dict(self.message_counts):
            messages = self.message_counts[channel_id]

            # Finds the highest applicable threshold
            slowmode_secs: float = CONST.AUTOSLOWMODE_DEFAULT
            for threshold in CONST.AUTOSLOWMODE_THRESHOLDS:
                if threshold[0] <= messages:
                    slowmode_secs = threshold[1] * CONST.AUTOSLOWMODE_CHANNELS[channel_id]
                    break

            slowmode_secs = int(slowmode_secs)

            channel = self.bot.get_channel(channel_id)

            if isinstance(channel, discord.TextChannel | discord.Thread):
                await channel.edit(slowmode_delay=slowmode_secs)

            logger.info(f"slowmode updated to {slowmode_secs}")
        self.message_counts.clear()


async def setup(bot: Tux) -> None:
    await bot.add_cog(SlowmodeHandler(bot))
