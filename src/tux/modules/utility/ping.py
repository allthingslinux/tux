"""
Bot status and ping checking commands.

This module provides commands to check the bot's latency, uptime, and system
resource usage information for monitoring bot health and performance.
"""

from datetime import UTC, datetime

import psutil
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.ui.embeds import EmbedCreator


class Ping(BaseCog):
    """Discord cog for checking bot status and ping."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Ping cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.hybrid_command(
        name="ping",
        aliases=["status"],
    )
    async def ping(self, ctx: commands.Context[Tux]) -> None:
        """
        Check the bot's latency and other stats.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The discord context object.
        """
        try:
            # Get the latency of the bot in milliseconds
            discord_ping = round(self.bot.latency * 1000)

            # Handles Time (turning POSIX time datetime)
            bot_start_time = datetime.fromtimestamp(self.bot.uptime, UTC)
            current_time = datetime.now(UTC)  # Get current time
            uptime_delta = current_time - bot_start_time

            # Convert it into Human comprehensible times
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Format it for the command
            bot_uptime_parts = [
                f"{days}d" if days else "",
                f"{hours}h" if hours else "",
                f"{minutes}m" if minutes else "",
                f"{seconds}s",
            ]
            bot_uptime_readable = " ".join(
                part for part in bot_uptime_parts if part
            ).strip()

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

        except (OSError, ValueError) as e:
            # Handle psutil errors gracefully
            discord_ping = round(self.bot.latency * 1000)
            bot_uptime_readable = "Unknown"
            cpu_usage = 0.0
            ram_amount_formatted = "Unknown"
            logger.warning(f"Failed to get system stats: {e}")

        embed = EmbedCreator.create_embed(
            embed_type=EmbedCreator.INFO,
            bot=self.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Pong!",
            description="Here are some stats about the bot.",
        )

        embed.add_field(name="API Latency", value=f"{discord_ping}ms", inline=True)
        embed.add_field(name="Uptime", value=f"{bot_uptime_readable}", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM Usage", value=f"{ram_amount_formatted}", inline=True)

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Set up the Ping cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Ping(bot))
