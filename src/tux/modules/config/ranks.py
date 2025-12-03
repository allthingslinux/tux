"""Rank management commands for the config system."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from tux.core.permission_system import DEFAULT_RANKS, get_permission_system

from .base import BaseConfigManager

if TYPE_CHECKING:
    from tux.core.bot import Tux


class RankManager(BaseConfigManager):
    """Management commands for permission ranks."""

    async def configure_ranks(self, ctx: commands.Context[Tux]) -> None:
        """
        View permission ranks using the unified config dashboard.

        This command launches the unified configuration dashboard in ranks mode
        where permission ranks are displayed and can be managed.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command invocation.
        """
        await self.configure_dashboard(ctx, "ranks")

    async def initialize_ranks(self, ctx: commands.Context[Tux]) -> None:
        """Initialize default permission ranks (0-7)."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if ranks already exist
            existing_ranks = (
                await self.bot.db.permission_ranks.get_permission_ranks_by_guild(
                    ctx.guild.id,
                )
            )
            if existing_ranks:
                embed = self.create_warning_embed(
                    "⚠️ Permission Ranks Already Exist",
                    (
                        f"This guild already has {len(existing_ranks)} permission ranks configured.\n\n"
                        "**Existing ranks will be preserved.**\n\n"
                        "Use the dashboard to modify existing ranks."
                    ),
                )
                await ctx.send(embed=embed)
                return

            # Initialize default ranks
            permission_system = get_permission_system()
            await permission_system.initialize_guild(ctx.guild.id)

            # Generate rank list from the default ranks
            rank_lines = [
                f"• **Rank {rank_num}**: {rank_data['name']}"
                for rank_num, rank_data in sorted(DEFAULT_RANKS.items())
            ]

            embed = self.create_success_embed(
                "✅ Permission Ranks Initialized",
                (
                    "Default permission ranks (0-7) have been created:\n\n"
                    + "\n".join(rank_lines)
                    + "\n\n"
                    + "Use `/config role assign` to assign Discord roles to these ranks."
                ),
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await self.handle_error(ctx, e, "initialize ranks")
