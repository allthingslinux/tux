import asyncio
import contextlib
from collections.abc import Mapping
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

# TODO: move this to a separate file


class TuxHelp(commands.HelpCommand):
    async def send_bot_help(
        self,
        mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
    ):
        """
        Sends help message for the bot.
        """
        embed = discord.Embed(
            title="Tux Help",
            color=discord.Color.blurple(),
        )

        category_strings = {}

        for cog, mapping_commands in mapping.items():
            for command in mapping_commands:
                if cog is None:
                    continue

                # get the category name
                category = cog.qualified_name
                # get the command name
                command_name = command.name

                # check if the category is already in the list
                if category not in category_strings:
                    category_strings[category] = f"**{category}** | "

                # add the command name to the list of commands for the category
                category_strings[category] += f"{command_name} "

        # set the description of the embed to the category strings
        embed.description = "\n".join(category_strings.values())

        await self.get_destination().send(embed=embed)


class TuxBot(commands.Bot):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.activity_changer = ActivityChanger(self)
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


async def main() -> None:
    # Setup Sentry for error tracking and reporting
    setup_sentry()

    prefix = CONST.DEV_PREFIX if CONST.DEV == "True" else CONST.PROD_PREFIX
    token = CONST.DEV_TOKEN if CONST.DEV == "True" else CONST.PROD_TOKEN

    # Initialize the bot
    bot = TuxBot(command_prefix=prefix, intents=discord.Intents.all())

    # Initialize the console and console task
    console = None
    console_task = None

    try:
        console = Console(bot)
        console_task = asyncio.create_task(console.run_console())

        # Start the bot and reconnect on disconnection
        await bot.start(token=token, reconnect=True)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down.")

    finally:
        logger.info("Closing resources.")
        await bot.shutdown()

        # Cancel the console task if it's still running
        if console_task is not None and not console_task.done():
            console_task.cancel()
            # Suppress the CancelledError exception
            with contextlib.suppress(asyncio.CancelledError):
                await console_task

    logger.info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        # Run the bot using asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully
        logger.info("Exiting gracefully.")
