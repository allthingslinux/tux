import discord
from discord.ext import commands
from tux_events.event_handler import EventHandler
import asyncio
import logging

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)

bot_prefix = '!'
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=bot_prefix, intents=intents)

event_handler = EventHandler(bot, True)


async def setup():
    bot = commands.Bot(command_prefix=bot_prefix, intents=intents)
    async with bot:
        await event_handler.setup(bot, True)
        await bot.start('MTE4MjE5NDU4NTY5OTYzMTEzNA.GUaYP5.qbUQSLvBYzZ6TsXP_P3Qx1RZiobPrCDgF3NWpQ',
                        reconnect=True)


@bot.event
async def on_ready():
    print(f'Bot is ready. Connected as {bot.user}')
    await setup()

asyncio.run(setup())
