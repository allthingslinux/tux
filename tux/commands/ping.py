# commands/ping.py

import time

from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """
        Checks the bot's latency.
        """
        # We record the time before we send a message
        start = time.time()

        message = await ctx.send("Pinging...")

        # The time after the message was sent
        end = time.time()

        # Discord Python calculates the latency and records it in the bot instance
        # It's done every minute so this won't hurt performance
        discord_ping = round(self.bot.latency * 1000)

        # The time it takes for the message to be sent
        message_ping = round((end - start) * 1000)
        await message.edit(
            content=f"Pong! 🏓\nDiscord API latency: {discord_ping}ms\nMessage latency: {message_ping}ms"
        )

        logger.info(f"{ctx.author} used {ctx.command} in {ctx.channel}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
