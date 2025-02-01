import asyncio
from typing import Any

from colorama import Back, Fore, Style
from discord.ext import commands
from loguru import logger

from tux.cog_loader import CogLoader
from tux.database.client import db
from tux.utils.config import Config


class Tux(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.setup_task = asyncio.create_task(self.setup())
        self.is_shutting_down = False

    async def setup(self) -> None:
        """
        Sets up the bot by connecting to the database and loading cogs.
        """

        try:
            # Connect to Prisma
            logger.info("Setting up Prisma client...")
            await db.connect()
            logger.info(f"Prisma client connected: {db.is_connected()}")
            logger.info(f"Prisma client registered: {db.is_registered()}")

        except Exception as e:
            logger.critical(f"An error occurred while connecting to the database: {e}")
            return

        # Load Jishaku for debugging
        await self.load_extension("jishaku")
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
        logger.info(f"""
    .--.      {Back.WHITE}{Fore.BLACK}{Config.BOT_NAME} (Tux) version {Config.BOT_VERSION} has started!{Style.RESET_ALL}
   |o_o |     Bot ID: {Style.DIM}{self.user.id if self.user else "Unknown"}{Style.RESET_ALL}
   |:_/ |     Watching {Style.DIM}{len(self.guilds)}{Style.RESET_ALL} servers with {Style.DIM}{len(self.users)}{Style.RESET_ALL} users
  //   \\ \\    Prefix: {Style.DIM}{Config.DEFAULT_PREFIX}{Style.RESET_ALL}
 (|     | )   Running in {f"{Fore.RED}Development" if Config.DEV else f"{Fore.GREEN}Production"}{Style.RESET_ALL} mode
/'\\_   _/`\\
\\___)=(___/ """)

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
            logger.info("Shutdown already in progress. Exiting.")
            return

        self.is_shutting_down = True
        logger.info("Shutting down...")

        await self.close()

        if tasks := [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]:
            logger.debug(f"Cancelling {len(tasks)} outstanding tasks: {', '.join([task.get_name() for task in tasks])}")

            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug("All tasks cancelled!")

        try:
            logger.debug("Closing database connections.")
            await db.disconnect()

        except Exception as e:
            logger.critical(f"Error during database disconnection: {e}")

        logger.info("Shutdown complete.")
