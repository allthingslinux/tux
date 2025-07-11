import psutil
from bot import Tux
from discord.ext import commands
from ui.embeds import EmbedCreator
from utils.functions import generate_usage


class Ping(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.ping.usage = generate_usage(self.ping)

    @commands.hybrid_command(
        name="ping",
    )
    async def ping(self, ctx: commands.Context[Tux]) -> None:
        """
        Check the bot's latency and other stats.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The discord context object.
        """

        # Get the latency of the bot in milliseconds
        discord_ping = round(self.bot.latency * 1000)

        # Get the CPU usage and RAM usage of the bot
        cpu_usage = psutil.Process().cpu_percent()
        # Get the amount of RAM used by the bot
        ram_amount_in_bytes = psutil.Process().memory_info().rss
        ram_amount_in_mb = ram_amount_in_bytes / (1024 * 1024)

        # Format the RAM usage to be in GB or MB, rounded to nearest integer
        if ram_amount_in_mb >= 1024:
            ram_amount_formatted = f"{round(ram_amount_in_mb / 1024)}GB"
        else:
            ram_amount_formatted = f"{round(ram_amount_in_mb)}MB"

        embed = EmbedCreator.create_embed(
            embed_type=EmbedCreator.INFO,
            bot=self.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Pong!",
            description="Here are some stats about the bot.",
        )

        embed.add_field(name="API Latency", value=f"{discord_ping}ms", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM Usage", value=f"{ram_amount_formatted}", inline=True)

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Ping(bot))
