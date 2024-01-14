from discord.ext import commands

from tux.command_cog import CommandCog
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Ping(CommandCog):
    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """
        Checks the bot's latency.
        """
        discord_ping = round(self.bot.latency * 1000)

        await self.bot.embed.send_embed(
            ctx.channel.id,
            title="Pong!",
            description=f"Discord ping: {discord_ping}ms",
        )

        logger.info(f"{ctx.author} used {ctx.command} in {ctx.channel}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
