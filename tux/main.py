import asyncio
import contextlib
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

"""
Advanced logging and debugging setup.
This setup is intended for debugging purposes. Ensure that you comment out loguru and replace it with the following imports as well as the remaining lines below.
"""
# import logging
# import warnings
# import tracemalloc

# tracemalloc.start()
# logging.basicConfig(level=logging.DEBUG)
# warnings.simplefilter("error", ResourceWarning)


class TuxBot(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.activity_changer = ActivityChanger(self)
        self.setup_task = asyncio.create_task(self.setup())
        self.is_shutting_down = False

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

        if not self.setup_task.done():
            await self.setup_task

        logger.info(f"{self.user} has connected to Discord!")

        activity_task = asyncio.create_task(self.activity_changer.run())

        await asyncio.gather(activity_task)

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        """
        Executes actions when the bot disconnects from Discord, such as closing the database connection.
        """
        logger.warning("Bot has disconnected from Discord.")

    async def shutdown(self):
        if self.is_shutting_down:
            logger.info("Shutdown already in progress. Exiting...")
            return
        self.is_shutting_down = True

        logger.info("Shutting down...")

        await self.close()

        if tasks := [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]:
            logger.info(f"Cancelling {len(tasks)} outstanding tasks")
            [task.cancel() for task in tasks]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("All tasks cancelled.")

        try:
            logger.info("Closing database connections...")
            await db.disconnect()
        except Exception as e:
            logger.error(f"Error during database disconnection: {e}")

        logger.info("Shutdown complete.")


async def main() -> None:
    setup_sentry()

    intents = discord.Intents.all()
    prefix = CONST.STAGING_PREFIX if CONST.STAGING == "True" else CONST.PROD_PREFIX
    token = CONST.STAGING_TOKEN if CONST.STAGING == "True" else CONST.PROD_TOKEN
    bot = TuxBot(command_prefix=prefix, intents=intents)

    console = None
    console_task = None

    try:
        console = Console(bot)
        console_task = asyncio.create_task(console.run_console())

        await bot.start(token=token, reconnect=True)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down.")

    finally:
        logger.info("Closing resources.")
        await bot.shutdown()

        if console_task is not None and not console_task.done():
            console_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await console_task

    logger.info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting gracefully.")
