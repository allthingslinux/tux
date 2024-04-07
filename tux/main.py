import asyncio
from typing import Any

import discord
from discord.ext import commands
from loguru import logger

from tux.cog_loader import CogLoader
from tux.database.client import db
from tux.utils.activities import ActivityChanger
from tux.utils.console import Console
from tux.utils.constants import Constants as CONST
from tux.utils.sentry import setup_sentry


class TuxBot(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.console = Console(self)
        self.activity_changer = ActivityChanger(self)
        self.setup_task = asyncio.create_task(self.setup())

    async def setup(self) -> None:
        """
        Performs setup tasks for the TuxBot, such as loading cogs.
        """
        try:
            await db.connect()
            logger.info("Database connection established.")
        except Exception as e:
            logger.error(f"An error occurred while connecting to the database: {e}")
            return

        await self.load_cogs()

    async def load_cogs(self) -> None:
        """
        Loads cogs by calling the setup method of CogLoader.
        """

        await CogLoader.setup(self)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Executes actions when the bot is ready, such as connecting to Discord and running tasks.
        """

        logger.info(f"{self.user} has connected to Discord!")

        activity_task = asyncio.create_task(self.activity_changer.run())
        console_task = asyncio.create_task(self.console.run_console())

        await asyncio.gather(activity_task, console_task)

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        """
        Executes actions when the bot disconnects from Discord, such as closing the database connection.
        """
        logger.warning("Bot has disconnected from Discord.")
        logger.warning("Database has been disconnected.")
        await db.disconnect()


async def main() -> None:
    try:
        setup_sentry()

        intents = discord.Intents.all()
        prefix = CONST.STAGING_PREFIX if CONST.STAGING == "True" else CONST.PROD_PREFIX
        token = CONST.STAGING_TOKEN if CONST.STAGING == "True" else CONST.PROD_TOKEN

        bot = TuxBot(command_prefix=prefix, intents=intents)
        await bot.start(token=token, reconnect=True)

    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
