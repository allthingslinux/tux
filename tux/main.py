import asyncio

import discord
from loguru import logger

from tux.client import Tux

# from tux.utils.console import Console
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


async def main() -> None:
    setup_sentry()

    prefix = CONST.PREFIX
    token = CONST.TOKEN

    # Initialize the bot
    bot = Tux(command_prefix=prefix, intents=discord.Intents.all())

    # Initialize the console and console task
    # console = None
    # console_task = None

    try:
        # console = Console(bot)
        # console_task = asyncio.create_task(console.run_console())

        # Start the bot and reconnect on disconnection
        await bot.start(token=token, reconnect=True)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down.")

    finally:
        logger.info("Closing resources.")
        await bot.shutdown()

        # Cancel the console task if it's still running
        # if console_task is not None and not console_task.done():
        # console_task.cancel()
        # Suppress the CancelledError exception
        # with contextlib.suppress(asyncio.CancelledError):
        # await console_task

    logger.info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        # Run the bot using asyncio
        asyncio.run(main())

    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully
        logger.info("Exiting gracefully.")
