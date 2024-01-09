# on_guild_channel_pins_update.py
from datetime import datetime

import discord
from discord.ext import commands
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnGuildChannelPinsUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(
        self,
        channel: discord.abc.GuildChannel | discord.Thread,
        last_pin: datetime | None,
    ):
        """
        Handles the event when a message is pinned or unpinned from a guild channel.

        This function is called whenever a message's pinned status is changed.

        Note:
            This function requires the `Intents.guilds` to be enabled.

        Args:
            channel (Union[discord.abc.GuildChannel, discord.Thread]): The guild channel or thread that had its pins updated.
            last_pin (Optional[datetime.datetime]): The time of the latest message that was pinned, in UTC.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_guild_channel_pins_update
        """  # noqa E501

        logger.info(f"Pins in  #{channel.name} have been updated. Last pin: {last_pin}")


async def setup(bot):
    await bot.add_cog(OnGuildChannelPinsUpdate(bot))
