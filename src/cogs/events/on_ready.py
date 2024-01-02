import discord
from discord.ext import bridge
from loguru import logger

class OnReady(discord.Cog):
    def __init__(self, bot: bridge.Bot) -> None:
        super().__init__()
        self.bot: bridge.Bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        return logger.info(f"{self.bot.user} has connected to Discord!")