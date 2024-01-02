import discord
from discord.ext import bridge
from loguru import logger
import os

intents = discord.Intents.all()
bot = bridge.Bot(command_prefix=">", intents=intents)


def load_cogs():
    [
        (
            bot.load_extension(f"cogs.{folder}.__init__"),
            logger.info(f"Loaded cogs.{folder}.__init__")[0],
        )
        for folder in os.listdir("cogs")
        if not "." in folder
    ]
    return


load_cogs()
bot.run(os.environ.get("TOKEN"))
