"""
Bot status and ping checking commands.

This module provides commands to check the bot's latency, uptime, and system
resource usage information for monitoring bot health and performance.
"""

import sys
from datetime import UTC, datetime, timedelta

import discord
import psutil
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.version import get_version


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
        self._process = psutil.Process()
        # Initialize CPU percent tracking (first call returns 0.0, needed for subsequent calls)
        self._process.cpu_percent(interval=None)

    def _format_uptime(self, uptime_delta: timedelta) -> str:
        """Format uptime delta into human-readable string.

        Parameters
        ----------
        uptime_delta : timedelta
            The uptime timedelta.

        Returns
        -------
        str
            Formatted uptime string.
        """
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        bot_uptime_parts = [
            f"{days}d" if days else "",
            f"{hours}h" if hours else "",
            f"{minutes}m" if minutes else "",
            f"{seconds}s",
        ]
        return " ".join(part for part in bot_uptime_parts if part).strip()

    def _get_system_stats(self) -> tuple[float, str, str, int | str, int | str]:
        """Get system resource statistics.

        Returns
        -------
        tuple[float, str, str, int | str, int | str]
            Tuple of (cpu_usage, ram_formatted, vms_formatted, pid, thread_count).
        """
        cpu_usage = self._process.cpu_percent(interval=None)
        if cpu_usage == 0.0:
            cpu_usage = self._process.cpu_percent(interval=0.3)

        mem_info = self._process.memory_info()
        ram_amount_in_mb = mem_info.rss / (1024 * 1024)
        vms_amount_in_gb = mem_info.vms / (1024 * 1024 * 1024)

        ram_formatted = (
            f"{round(ram_amount_in_mb / 1024)}GB"
            if ram_amount_in_mb >= 1024
            else f"{round(ram_amount_in_mb)}MB"
        )
        vms_formatted = f"{vms_amount_in_gb:.2f}GB"

        return (
            cpu_usage,
            ram_formatted,
            vms_formatted,
            self._process.pid,
            self._process.num_threads(),
        )

    def _get_bot_stats(self) -> tuple[int, int, bool, bool, bool, str]:
        """Get bot statistics and intents.

        Returns
        -------
        tuple[int, int, bool, bool, bool, str]
            Tuple of (guild_count, user_count, presences, members, message_content, shard_info).
        """
        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)
        intents = self.bot.intents
        is_sharded = self.bot.shard_count is not None and self.bot.shard_count > 1
        shard_info = f"{self.bot.shard_count} shards" if is_sharded else "Not sharded"

        return (
            guild_count,
            user_count,
            intents.presences,
            intents.members,
            intents.message_content,
            shard_info,
        )

    def _build_status_view(
        self,
        discord_ping: int,
        latency_emoji: str,
        bot_uptime_readable: str,
        shard_info: str,
        cpu_usage: float,
        ram_formatted: str,
        vms_formatted: str,
        pid: int | str,
        thread_count: int | str,
        guild_count: int,
        user_count: int,
        presences_enabled: bool,
        members_enabled: bool,
        message_content_enabled: bool,
    ) -> discord.ui.LayoutView:
        """Build the status display view.

        Parameters
        ----------
        discord_ping : int
            Discord latency in milliseconds.
        latency_emoji : str
            Emoji for latency status.
        bot_uptime_readable : str
            Human-readable uptime string.
        shard_info : str
            Sharding information.
        cpu_usage : float
            CPU usage percentage.
        ram_formatted : str
            Formatted RAM usage.
        vms_formatted : str
            Formatted virtual memory usage.
        pid : int | str
            Process ID.
        thread_count : int | str
            Thread count.
        guild_count : int
            Number of guilds.
        user_count : int
            Number of users.
        presences_enabled : bool
            Whether presences intent is enabled.
        members_enabled : bool
            Whether members intent is enabled.
        message_content_enabled : bool
            Whether message content intent is enabled.

        Returns
        -------
        discord.ui.LayoutView
            The built status view.
        """
        view = discord.ui.LayoutView(timeout=None)
        container = discord.ui.Container(accent_color=0x5865F2)  # type: ignore[type-arg]

        container.add_item(
            discord.ui.TextDisplay("# 🏓 Pong!\n\nHere are some stats about the bot."),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(
            discord.ui.TextDisplay(
                f"### 🌐 Connection & Performance\n"
                f"{latency_emoji} **Latency:** `{discord_ping}ms` • "
                f"⏱️ **Uptime:** `{bot_uptime_readable}` • "
                f"🔗 **Sharding:** `{shard_info}`",
            ),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(
            discord.ui.TextDisplay(
                f"### 💻 System Resources\n"
                f"⚙️ **CPU:** `{cpu_usage:.2f}%` • "
                f"💾 **RAM:** `{ram_formatted}` • "
                f"📊 **Virt:** `{vms_formatted}`\n"
                f"🔢 **PID:** `{pid}` • "
                f"🧵 **Threads:** `{thread_count}`",
            ),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(
            discord.ui.TextDisplay(
                f"### 🤖 Bot Statistics\n"
                f"🏠 **Guilds:** `{guild_count}` • "
                f"👥 **Users:** `{user_count}`",
            ),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(
            discord.ui.TextDisplay(
                f"### 🔐 Gateway Intents\n"
                f"👤 **Presences:** {'✅' if presences_enabled else '❌'} • "
                f"👥 **Members:** {'✅' if members_enabled else '❌'} • "
                f"💬 **Message Content:** {'✅' if message_content_enabled else '❌'}",
            ),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        tux_version = get_version()
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        discord_py_version = discord.__version__

        container.add_item(
            discord.ui.TextDisplay(
                f"### 📦 Versions\n"
                f"🐧 **Tux:** `{tux_version}` • "
                f"🐍 **Python:** `{python_version}` • "
                f"👾 **discord.py:** `{discord_py_version}`",
            ),
        )

        view.add_item(container)  # type: ignore[arg-type]
        return view

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
        await ctx.defer(ephemeral=True)

        discord_ping = round(self.bot.latency * 1000)

        bot_start_time = datetime.fromtimestamp(self.bot.uptime, UTC)
        uptime_delta = datetime.now(UTC) - bot_start_time
        bot_uptime_readable = self._format_uptime(uptime_delta)

        try:
            cpu_usage, ram_formatted, vms_formatted, pid, thread_count = (
                self._get_system_stats()
            )
        except (OSError, ValueError) as e:
            logger.warning(f"Failed to get system stats: {e}")
            cpu_usage = 0.0
            ram_formatted = "Unknown"
            vms_formatted = "Unknown"
            pid = "Unknown"
            thread_count = "Unknown"

        (
            guild_count,
            user_count,
            presences_enabled,
            members_enabled,
            message_content_enabled,
            shard_info,
        ) = self._get_bot_stats()

        latency_emoji = (
            "🟢" if discord_ping < 100 else "🟡" if discord_ping < 200 else "🔴"
        )

        view = self._build_status_view(
            discord_ping,
            latency_emoji,
            bot_uptime_readable,
            shard_info,
            cpu_usage,
            ram_formatted,
            vms_formatted,
            pid,
            thread_count,
            guild_count,
            user_count,
            presences_enabled,
            members_enabled,
            message_content_enabled,
        )

        if ctx.interaction:
            await ctx.interaction.followup.send(view=view, ephemeral=True)
        else:
            await ctx.send(view=view)


async def setup(bot: Tux) -> None:
    """Set up the Ping cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Ping(bot))
