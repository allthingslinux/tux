import discord
from discord.ext import commands
from tux_events.event_handler import EventHandler
import asyncio
import logging
from tux_utils.tux_logger import setup, TuxLogger

logger = TuxLogger(__name__)

bot_prefix = '!'
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=bot_prefix, intents=intents)

# Call the setup function once
asyncio.run(setup(bot, project_logging_level=logging.DEBUG, discord_logging_level=logging.WARNING))
event_handler = EventHandler(bot, True)


async def main():
    async with bot:
        # Add debugging statements
        print("Setting up event handler...")
        await event_handler.setup(bot, True)
        print("Event handler setup completed.")

        await bot.start(
            'TOKEN',
            reconnect=True
        )

# Only run asyncio.run(main()) once, as it's the entry point for the application
asyncio.run(main())

