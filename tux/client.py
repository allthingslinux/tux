import asyncio
from typing import Any

from discord.ext import commands
from loguru import logger

from tux.cog_loader import CogLoader
from tux.database.client import db
from tux.help import TuxHelp


class Tux(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.setup_task = asyncio.create_task(self.setup())
        self.is_shutting_down = False
        self.help_command = TuxHelp()

    async def setup(self) -> None:
        """
        Sets up the bot by connecting to the database and loading cogs.
        """

        try:
            # Connect to Prisma
            await db.connect()
            logger.info("Database connection established.")

        except Exception as e:
            logger.error(f"An error occurred while connecting to the database: {e}")
            return

        # Load cogs via CogLoader
        await self.load_cogs()

    async def load_cogs(self) -> None:
        """
        Loads cogs by calling the setup method of CogLoader.
        """

        logger.info("Loading cogs...")
        await CogLoader.setup(self)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Executes actions when the bot is ready, such as connecting to Discord and running tasks.
        """
        logger.info(f"{self.user} has connected to Discord!")

        if not self.setup_task.done():
            await self.setup_task

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        """
        Executes actions when the bot disconnects from Discord.
        """
        logger.warning("Bot has disconnected from Discord.")

    async def shutdown(self) -> None:
        if self.is_shutting_down:
            logger.info("Shutdown already in progress. Exiting...")
            return

        self.is_shutting_down = True
        logger.info("Shutting down...")

        await self.close()

        # Cancel all tasks except the current one
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
