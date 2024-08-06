import psutil
from discord.ext import commands

from tux.utils.embeds import EmbedCreator


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        usage="$ping",
    )
    async def ping(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Check the bot's latency and other stats.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        """

        # Get the latency of the bot in milliseconds
        discord_ping = round(self.bot.latency * 1000)

        # Get the CPU usage and RAM usage of the bot
        cpu_usage = psutil.cpu_percent()
        # Get the amount of RAM used by the bot
        ram_amount = psutil.virtual_memory().used

        # Format the RAM usage to be in GB or MB
        if ram_amount >= 1024**3:
            ram_amount_formatted = f"{ram_amount // (1024**3)}GB"
        else:
            ram_amount_formatted = f"{ram_amount // (1024**2)}MB"

        embed = EmbedCreator.create_success_embed(
            title="Pong!",
            description="Here are some stats about the bot.",
            ctx=ctx,
        )

        embed.add_field(name="API Latency", value=f"{discord_ping}ms", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM Usage", value=f"{ram_amount_formatted}", inline=True)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))
