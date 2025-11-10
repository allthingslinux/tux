"""Role management commands for the config system."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from tux.database.models.models import PermissionAssignment

from .base import BaseConfigManager

if TYPE_CHECKING:
    from tux.core.bot import Tux


class RoleManager(BaseConfigManager):
    """Management commands for role-to-rank assignments."""

    async def configure_roles(self, ctx: commands.Context[Tux]) -> None:
        """
        Configure role permissions using the unified config dashboard.

        This command launches the unified configuration dashboard in roles mode
        to allow administrators to assign Discord roles to permission ranks.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command invocation.
        """
        await self.configure_dashboard(ctx, "roles")

    async def list_assignments(self, ctx: commands.Context[Tux]) -> None:
        """View all role-to-rank assignments."""
        assert ctx.guild

        await ctx.defer()

        assignments = await self.bot.db.permission_assignments.get_assignments_by_guild(ctx.guild.id)

        if not assignments:
            embed = self.create_error_embed(
                "❌ No Role Assignments",
                "No roles have been assigned to permission ranks.\n\nUse `/config role assign <rank> @Role` to assign roles.",
            )
            await ctx.send(embed=embed)
            return

        embed = self.create_info_embed(
            f"👥 Role Assignments - {ctx.guild.name}",
            f"Total: {len(assignments)} role assignments",
        )

        # Group by rank
        by_rank: dict[int, list[str]] = {}
        for assignment in assignments:
            rank = assignment.permission_rank_id
            role = ctx.guild.get_role(assignment.role_id)
            role_name = role.mention if role else f"Unknown Role ({assignment.role_id})"
            if rank not in by_rank:
                by_rank[rank] = []
            by_rank[rank].append(role_name)

        for rank in sorted(by_rank.keys()):
            role_list = by_rank[rank]
            embed.add_field(
                name=f"Rank {rank}",
                value="\n".join(role_list),
                inline=True,
            )

        embed.set_footer(text="Use /config role assign | unassign to manage assignments")
        await ctx.send(embed=embed)

    async def assign_role(self, ctx: commands.Context[Tux], rank: int, role: discord.Role) -> None:
        """Assign permission rank to Discord role."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if rank exists
            rank_obj = await self.bot.db.permission_ranks.get_permission_rank(ctx.guild.id, rank)
            if not rank_obj:
                embed = self.create_error_embed(
                    "❌ Rank Not Found",
                    f"Permission rank {rank} does not exist.\n\nUse `/config ranks list` to see available ranks.",
                )
                await ctx.send(embed=embed)
                return

            # Check if role is already assigned to this rank
            existing = await self.bot.db.permission_assignments.find_one(
                filters=(PermissionAssignment.guild_id == ctx.guild.id) & (PermissionAssignment.role_id == role.id),
            )
            if existing and existing.permission_rank_id == rank:
                embed = self.create_warning_embed(
                    "⚠️ Already Assigned",
                    f"Role {role.mention} is already assigned to rank {rank} (**{rank_obj.name}**).",
                )
                await ctx.send(embed=embed)
                return

            # Remove existing assignment if any
            if existing:
                await self.bot.db.permission_assignments.remove_role_assignment(ctx.guild.id, role.id)

            # Create new assignment
            await self.bot.db.permission_assignments.assign_permission_rank(
                guild_id=ctx.guild.id,
                permission_rank_id=rank,
                role_id=role.id,
            )

            embed = self.create_success_embed(
                "✅ Role Assigned",
                f"Role {role.mention} has been assigned to rank **{rank}** (**{rank_obj.name}**).",
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await self.handle_error(ctx, e, "assign role")

    async def unassign_role(self, ctx: commands.Context[Tux], role: discord.Role) -> None:
        """Remove permission rank from role."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if role has an assignment
            assignment = await self.bot.db.permission_assignments.find_one(
                filters=(PermissionAssignment.guild_id == ctx.guild.id) & (PermissionAssignment.role_id == role.id),
            )
            if not assignment:
                embed = self.create_error_embed(
                    "❌ No Assignment Found",
                    f"Role {role.mention} is not assigned to any permission rank.",
                )
                await ctx.send(embed=embed)
                return

            # Get rank info for display
            rank_obj = await self.bot.db.permission_ranks.get_permission_rank(
                ctx.guild.id,
                assignment.permission_rank_id,
            )
            rank_name = rank_obj.name if rank_obj else f"Rank {assignment.permission_rank_id}"

            # Remove assignment
            await self.bot.db.permission_assignments.remove_role_assignment(ctx.guild.id, role.id)

            embed = self.create_success_embed(
                "✅ Role Unassigned",
                f"Role {role.mention} has been removed from rank **{assignment.permission_rank_id}** (**{rank_name}**).",
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await self.handle_error(ctx, e, "unassign role")
