"""Main config cog implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

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
    async def config_overview(self, ctx: commands.Context[Tux]) -> None:
        """View complete guild configuration overview."""
        await self.overview.overview_command(ctx)

    @config.group(name="ranks")
    @commands.guild_only()
    async def ranks_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage permission ranks in this guild."""
        if ctx.invoked_subcommand is None:
            # Open the dashboard in roles mode (ranks are displayed there)
            await self.ranks.configure_ranks(ctx)

    @ranks_group.command(name="list")
    @commands.guild_only()
    async def ranks_list(self, ctx: commands.Context[Tux]) -> None:
        """List all permission ranks in this guild."""
        await self.ranks.list_ranks(ctx)

    @ranks_group.command(name="init")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ranks_init(self, ctx: commands.Context[Tux]) -> None:
        """Initialize default permission ranks (0-7)."""
        await self.ranks.initialize_ranks(ctx)

    @ranks_group.command(name="create")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ranks_create(
        self,
        ctx: commands.Context[Tux],
        rank: int,
        name: str,
        description: str | None = None,
    ) -> None:
        """Create a custom permission rank."""
        await self.ranks.create_rank(ctx, rank, name, description)

    @ranks_group.command(name="delete")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ranks_delete(self, ctx: commands.Context[Tux], rank: int) -> None:
        """Delete a custom permission rank."""
        await self.ranks.delete_rank(ctx, rank)

    @config.group(name="roles", aliases=["role"])
    @commands.guild_only()
    async def roles_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage role-to-rank assignments."""
        if ctx.invoked_subcommand is None:
            # Open the dashboard in roles mode
            await self.roles.configure_roles(ctx)

    @roles_group.command(name="list")
    @commands.guild_only()
    async def roles_list(self, ctx: commands.Context[Tux]) -> None:
        """View all role-to-rank assignments."""
        await self.roles.list_assignments(ctx)

    @roles_group.command(name="assign")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def roles_assign(self, ctx: commands.Context[Tux], rank: int, role: discord.Role) -> None:
        """Assign permission rank to Discord role."""
        await self.roles.assign_role(ctx, rank, role)

    @roles_group.command(name="unassign")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def roles_unassign(self, ctx: commands.Context[Tux], role: discord.Role) -> None:
        """Remove permission rank from role."""
        await self.roles.unassign_role(ctx, role)

    @config.group(name="commands")
    @commands.guild_only()
    async def commands_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage command permission requirements."""
        if ctx.invoked_subcommand is None:
            # Open the dashboard in commands mode
            await self.commands.configure_commands(ctx)

    @commands_group.command(name="list")
    @commands.guild_only()
    async def commands_list(self, ctx: commands.Context[Tux]) -> None:
        """View all command permission requirements."""
        await self.commands.list_permissions(ctx)

    @commands_group.command(name="assign")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def commands_assign(
        self,
        ctx: commands.Context[Tux],
        command_name: str,
        rank: int,
    ) -> None:
        """Set permission rank requirement for command."""
        await self.commands.assign_permission(ctx, command_name, rank)

    @commands_group.command(name="unassign")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def commands_unassign(self, ctx: commands.Context[Tux], command_name: str) -> None:
        """Remove permission requirement from command."""
        await self.commands.remove_permission(ctx, command_name)

    @config.command(name="logs")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx: commands.Context[Tux]) -> None:
        """Configure log channel assignments."""
        await self.log_manager.configure_logs(ctx)


async def setup(bot: Tux) -> None:
    """Load the Config cog."""
    await bot.add_cog(Config(bot))
