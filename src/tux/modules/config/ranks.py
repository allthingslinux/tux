"""Rank management commands for the config system."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from tux.core.permission_system import get_permission_system

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

    async def list_ranks(self, ctx: commands.Context[Tux]) -> None:
        """List all permission ranks in this guild."""
        assert ctx.guild

        await ctx.defer()

        ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(ctx.guild.id)

        if not ranks:
            embed = self.create_error_embed(
                "❌ No Permission Ranks",
                "No permission ranks found.\n\nUse `/config ranks init` to create default ranks.",
            )
            await ctx.send(embed=embed)
            return

        embed = self.create_info_embed(
            f"🎯 Permission Ranks - {ctx.guild.name}",
            f"Total: {len(ranks)} ranks configured",
        )

        status_icon = "✅"

        for rank in sorted(ranks, key=lambda x: x.rank):
            level_title = f"{status_icon} Rank {rank.rank}: {rank.name}"

            desc_parts = [rank.description or "*No description*"]

            embed.add_field(
                name=level_title,
                value=" | ".join(desc_parts),
                inline=False,
            )

        embed.set_footer(text="Use /config ranks init | create | delete to manage ranks")
        await ctx.send(embed=embed)

    async def initialize_ranks(self, ctx: commands.Context[Tux]) -> None:
        """Initialize default permission ranks (0-7)."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if ranks already exist
            existing_ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(ctx.guild.id)
            if existing_ranks:
                embed = self.create_warning_embed(
                    "⚠️ Permission Ranks Already Exist",
                    (
                        f"This guild already has {len(existing_ranks)} permission ranks configured.\n\n"
                        "**Existing ranks will be preserved.**\n\n"
                        "If you need to modify ranks, use:\n"
                        "• `/config ranks create` - Add new ranks\n"
                        "• `/config ranks delete` - Remove ranks"
                    ),
                )
                await ctx.send(embed=embed)
                return

            # Initialize default ranks
            permission_system = get_permission_system()
            await permission_system.initialize_guild(ctx.guild.id)

            embed = self.create_success_embed(
                "✅ Permission Ranks Initialized",
                (
                    "Default permission ranks (0-7) have been created:\n\n"
                    "• **Rank 0**: Everyone (default)\n"
                    "• **Rank 1**: Trusted\n"
                    "• **Rank 2**: Junior Moderator\n"
                    "• **Rank 3**: Moderator\n"
                    "• **Rank 4**: Senior Moderator\n"
                    "• **Rank 5**: Administrator\n"
                    "• **Rank 6**: Head Administrator\n"
                    "• **Rank 7**: Server Owner\n\n"
                    "Use `/config role assign` to assign Discord roles to these ranks."
                ),
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await self.handle_error(ctx, e, "initialize ranks")

    async def create_rank(
        self,
        ctx: commands.Context[Tux],
        rank: int,
        name: str,
        description: str | None = None,
    ) -> None:
        """Create a custom permission rank."""
        assert ctx.guild

        await ctx.defer()

        if not 0 <= rank <= 10:
            embed = self.create_error_embed("❌ Invalid Rank", "Rank must be between 0 and 10.")
            await ctx.send(embed=embed)
            return

        try:
            # Check if rank already exists
            existing = await self.bot.db.permission_ranks.get_permission_rank(ctx.guild.id, rank)
            if existing:
                embed = self.create_error_embed(
                    "❌ Rank Already Exists",
                    f"Rank {rank} already exists: **{existing.name}**",
                )
                await ctx.send(embed=embed)
                return

            # Create the rank
            await self.bot.db.permission_ranks.create_permission_rank(
                guild_id=ctx.guild.id,
                rank=rank,
                name=name,
                description=description or "",
            )

            embed = self.create_success_embed(
                "✅ Permission Rank Created",
                f"Created rank **{rank}**: **{name}**\n\nUse `/config role assign {rank} @Role` to assign roles to this rank.",
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await self.handle_error(ctx, e, "create rank")

    async def delete_rank(self, ctx: commands.Context[Tux], rank: int) -> None:
        """Delete a permission rank."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if rank exists
            existing = await self.bot.db.permission_ranks.get_permission_rank(ctx.guild.id, rank)
            if not existing:
                embed = self.create_error_embed("❌ Rank Not Found", f"Rank {rank} does not exist.")
                await ctx.send(embed=embed)
                return

            # Delete the rank
            await self.bot.db.permission_ranks.delete_permission_rank(ctx.guild.id, rank)

            embed = self.create_success_embed(
                "✅ Permission Rank Deleted",
                f"Deleted rank **{rank}**: **{existing.name}**",
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await self.handle_error(ctx, e, "delete rank")
