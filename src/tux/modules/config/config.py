"""Main config cog implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from tux.core.decorators import requires_command_permission

from .commands import CommandManager
from .logs import LogManager
from .overview import ConfigOverview
from .ranks import RankManager
from .roles import RoleManager

if TYPE_CHECKING:
    from tux.core.bot import Tux


class Config(commands.Cog):
    """Comprehensive guild configuration and setup system."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Config cog with all sub-modules.

        Parameters
        ----------
        bot : Tux
            The bot instance to initialize the config cog with.
        """
        self.bot = bot

        # Initialize sub-modules
        self.overview = ConfigOverview(bot)
        # Initialize specialized managers for different config areas
        self.ranks = RankManager(bot)
        self.roles = RoleManager(bot)
        self.commands = CommandManager(bot)
        self.log_manager = LogManager(bot)

    @commands.hybrid_group(
        name="config",
        aliases=["settings"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def config(self, ctx: commands.Context[Tux]) -> None:
        """Manage the configuration of this guild."""
        if ctx.invoked_subcommand is None:
            # Open the dashboard overview
            await self.overview.overview_command(ctx)

    @config.command(
        name="overview",
        aliases=["dashboard"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def config_overview(self, ctx: commands.Context[Tux]) -> None:
        """View complete guild configuration overview."""
        await self.overview.overview_command(ctx)

    @config.group(name="ranks")
    @commands.guild_only()
    @requires_command_permission()
    async def ranks_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage permission ranks in this guild."""
        if ctx.invoked_subcommand is None:
            # Open the dashboard in roles mode (ranks are displayed there)
            await self.ranks.configure_ranks(ctx)

    @ranks_group.command(name="init")
    @commands.guild_only()
    @requires_command_permission()
    async def ranks_init(self, ctx: commands.Context[Tux]) -> None:
        """Initialize default permission ranks (0-7)."""
        await self.ranks.initialize_ranks(ctx)

    @config.group(name="roles", aliases=["role"])
    @commands.guild_only()
    @requires_command_permission()
    async def roles_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage role-to-rank assignments."""
        if ctx.invoked_subcommand is None:
            # Open the dashboard in roles mode
            await self.roles.configure_roles(ctx)

    @config.group(name="commands")
    @commands.guild_only()
    @requires_command_permission()
    async def commands_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage command permission requirements."""
        if ctx.invoked_subcommand is None:
            # Open the dashboard in commands mode
            await self.commands.configure_commands(ctx)

    @config.command(name="logs")
    @commands.guild_only()
    @requires_command_permission()
    async def logs(self, ctx: commands.Context[Tux]) -> None:
        """Configure log channel assignments."""
        await self.log_manager.configure_logs(ctx)


async def setup(bot: Tux) -> None:
    """Load the Config cog."""
    await bot.add_cog(Config(bot))
