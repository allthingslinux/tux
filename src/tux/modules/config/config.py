"""Main config cog implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from .management import ConfigManagement
from .overview import ConfigOverview
from .wizard import ConfigWizard

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
        self.management = ConfigManagement(bot)
        self.wizard = ConfigWizard(bot)

    @commands.hybrid_group(name="config")
    @commands.guild_only()
    async def config(self, ctx: commands.Context[Tux]) -> None:
        """View complete guild configuration overview."""
        await self.overview.overview_command(ctx)

    @config.command(name="wizard")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config_wizard(self, ctx: commands.Context[Tux]) -> None:
        """Launch the interactive setup wizard."""
        await self.wizard.wizard_command(ctx)

    @config.command(name="reset")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config_reset(self, ctx: commands.Context[Tux]) -> None:
        """Reset guild setup to allow re-running the wizard."""
        await self.wizard.reset_command(ctx)

    @config.group(name="rank")
    @commands.guild_only()
    async def rank(self, ctx: commands.Context[Tux]) -> None:
        """List all permission ranks in this guild."""
        await self.management.rank_list_command(ctx)

    @rank.command(name="init")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def rank_init(self, ctx: commands.Context[Tux]) -> None:
        """Initialize default permission ranks (0-7)."""
        await self.management.rank_init_command(ctx)

    @rank.command(name="create")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def rank_create(
        self,
        ctx: commands.Context[Tux],
        rank: int,
        name: str,
        description: str | None = None,
    ) -> None:
        """Create a custom permission rank."""
        await self.management.rank_create_command(ctx, rank, name, description)

    @rank.command(name="delete")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def rank_delete(self, ctx: commands.Context[Tux], rank: int) -> None:
        """Delete a custom permission rank."""
        await self.management.rank_delete_command(ctx, rank)

    @config.group(name="role")
    @commands.guild_only()
    async def role(self, ctx: commands.Context[Tux]) -> None:
        """View all role-to-rank assignments."""
        await self.management.role_list_command(ctx)

    @role.command(name="assign")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def role_assign(self, ctx: commands.Context[Tux], rank: int, role: discord.Role) -> None:
        """Assign permission rank to Discord role."""
        await self.management.role_assign_command(ctx, rank, role)

    @role.command(name="unassign")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def role_unassign(self, ctx: commands.Context[Tux], role: discord.Role) -> None:
        """Remove permission rank from role."""
        await self.management.role_unassign_command(ctx, role)

    @config.group(name="command")
    @commands.guild_only()
    async def command(self, ctx: commands.Context[Tux]) -> None:
        """View all command permission requirements."""
        await self.management.command_list_command(ctx)

    @command.command(name="assign")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def command_assign(
        self,
        ctx: commands.Context[Tux],
        command_name: str,
        rank: int,
    ) -> None:
        """Set permission rank requirement for command."""
        await self.management.command_assign_command(ctx, command_name, rank)

    @command.command(name="unassign")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def command_unassign(self, ctx: commands.Context[Tux], command_name: str) -> None:
        """Remove permission requirement from command."""
        await self.management.command_unassign_command(ctx, command_name)


async def setup(bot: Tux) -> None:
    """Load the Config cog."""
    await bot.add_cog(Config(bot))
