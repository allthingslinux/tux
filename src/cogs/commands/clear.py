import discord
from discord.ext import bridge
from loguru import logger

class Clear(discord.Cog):
    def __init__(self, bot: bridge.Bot) -> None:
        super().__init__()
        self.bot = bot

    @bridge.bridge_command()
    @bridge.has_permissions(administrator=True)
    async def clear(self, ctx: bridge.BridgeContext | discord.ApplicationContext, amount: int = 100):
        await ctx.channel.purge(limit=amount)
        logger.info(f"{ctx.author} cleared the channel {ctx.channel}.")