import asyncio

import discord
from loguru import logger

from tux.bot import Tux

# from tux.utils.console import Console
from tux.utils.constants import Constants as CONST
from tux.utils.sentry import setup_sentry

# if CONST.DEBUG is True:
#     import logging
#     import tracemalloc
#     import warnings

#     tracemalloc.start()
#     logging.basicConfig(level=logging.DEBUG)
#     warnings.simplefilter("error", ResourceWarning)


async def main() -> None:
    # Initialize the console and console task
    # console = None
    # console_task = None

    # Initialize the bot
    bot = Tux(command_prefix=CONST.PREFIX, intents=discord.Intents.all())

    setup_sentry(bot)

    try:
        # console = Console(bot)
        # console_task = asyncio.create_task(console.run_console())

        # Start the bot and reconnect on disconnection
        await bot.start(token=CONST.TOKEN, reconnect=True)

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
