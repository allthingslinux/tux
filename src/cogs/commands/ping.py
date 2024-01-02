import discord
from discord.ext import bridge

class Ping(discord.Cog):
    def __init__(self, bot):
        self.bot: bridge.Bot = bot

    @bridge.bridge_command()
    async def ping(self, ctx: bridge.BridgeContext):
        """Checks the latency of the bot."""
        await ctx.respond(f"Pong!\nLatency: {round(self.bot.latency * 1000)}ms")