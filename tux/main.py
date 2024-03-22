import asyncio
import os

import discord
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

from tux.cog_loader import CogLoader
from tux.permissions import Permissions
from tux.utils.tux_logger import TuxLogger

load_dotenv()

logger = TuxLogger(__name__)


class TuxBot(commands.Bot):
    """
    TuxBot is a custom bot class that extends commands.Bot from discord.ext.
    """

    def __init__(self, intents, command_prefix="/", **options) -> None:
        """
        Constructor for the TuxBot class.

        Args:
        - command_prefix (str): The prefix that triggers bot commands.
        - intents (discord.Intents): The intents to enable for the bot.
        """
        self.permissions = Permissions()
        super().__init__(command_prefix=command_prefix, intents=intents, **options)
        asyncio.create_task(self.setup())

    async def setup(self) -> None:
        """
        Additional setup for the bot, including loading cogs and setting up event handlers.
        """
        await self.load_cogs()
        await self.add_event_handler()

    async def load_cogs(self) -> None:
        """
        Load cogs for the bot via cog_loader.py
        """
        await CogLoader.setup(self, debug=True)
        logger.debug("Cog loader setup completed.")

    async def add_event_handler(self) -> None:
        """
        Add event handlers for the bot.
        """

        @self.event
        async def on_ready() -> None:
            """
            Event triggered when the bot is ready.
            """
            logger.info(f"{self.user} has connected to Discord!", __name__)

            # Set the bot's status
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="All Things Linux",
                )
            )

        @self.event
        async def on_disconnect() -> None:
            """
            Event triggered when the bot is disconnected.
            """
            logger.info(f"{self.user} has disconnected from Discord!", __name__)


async def main() -> None:
    try:
        bot_prefix = ">"
        intents: Intents = discord.Intents.all()
        bot = TuxBot(intents=intents, command_prefix=bot_prefix)
        await bot.start(token=os.getenv("TOKEN") or "", reconnect=True)
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
