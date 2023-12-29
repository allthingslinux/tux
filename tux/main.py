import asyncio
import logging

import discord
from discord.ext import commands
from tux_events.event_handler import EventHandler
from tux_utils.tux_logger import TuxLogger, setup

logger = TuxLogger(__name__)

bot_prefix = "!"
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=bot_prefix, intents=intents)

asyncio.run(
    setup(
        bot, project_logging_level=logging.DEBUG, discord_logging_level=logging.WARNING
    )
)
event_handler = EventHandler(bot, True)


async def main():
    async with bot:
        logger.debug("Setting up event handler...")
        await event_handler.setup(bot, True)
        logger.debug("Event handler setup completed.")

        await bot.start(
            "MTE4MjE5NDU4NTY5OTYzMTEzNA.GUaYP5.qbUQSLvBYzZ6TsXP_P3Qx1RZiobPrCDgF3NWpQ",
            reconnect=True,
        )

    @commands.Cog.listener()
    async def on_ready(self):
        """
        This function is called when the bot successfully connects to Discord.
        """
        logger.info(f"{self.bot.user} has connected to Discord!", __name__)


asyncio.run(main())
