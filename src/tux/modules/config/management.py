"""Configuration management commands for ranks, roles, and commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from tux.core.permission_system import get_permission_system
from tux.database.models.models import PermissionAssignment, PermissionCommand
from tux.ui.embeds import EmbedCreator, EmbedType

if TYPE_CHECKING:
    from tux.core.bot import Tux


class ConfigManagement:
    """Management commands for config system."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the ConfigManagement with a bot instance.

        Parameters
        ----------
        bot : Tux
            The bot instance to use for database operations.
        """
        self.bot = bot

    async def rank_list_command(self, ctx: commands.Context[Tux]) -> None:
        """List all permission ranks in this guild."""
        assert ctx.guild

        await ctx.defer()

        ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(ctx.guild.id)

        if not ranks:
            embed = EmbedCreator.create_embed(
                title="❌ No Permission Ranks",
                description="No permission ranks found.\n\nUse `/config rank init` to create default ranks.",
                embed_type=EmbedType.ERROR,
                custom_color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        embed = EmbedCreator.create_embed(
            title=f"🎯 Permission Ranks - {ctx.guild.name}",
            description=f"Total: {len(ranks)} ranks configured",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
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

        embed.set_footer(text="Use /config rank init | create | delete to manage ranks")
        await ctx.send(embed=embed)

    async def rank_init_command(self, ctx: commands.Context[Tux]) -> None:
        """Initialize default permission ranks (0-7)."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if ranks already exist
            existing_ranks = await self.bot.db.permission_ranks.get_permission_ranks_by_guild(ctx.guild.id)
            if existing_ranks:
                embed = EmbedCreator.create_embed(
                    title="⚠️ Permission Ranks Already Exist",
                    description=(
                        f"This guild already has {len(existing_ranks)} permission ranks configured.\n\n"
                        "**Existing ranks will be preserved.**\n\n"
                        "If you need to modify ranks, use:\n"
                        "• `/config rank create` - Add new ranks\n"
                        "• `/config rank delete` - Remove ranks"
                    ),
                    embed_type=EmbedType.WARNING,
                )
                await ctx.send(embed=embed)
                return

            # Initialize default ranks
            permission_system = get_permission_system()
            await permission_system.initialize_guild(ctx.guild.id)

            embed = EmbedCreator.create_embed(
                title="✅ Permission Ranks Initialized",
                description=(
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
                embed_type=EmbedType.SUCCESS,
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = EmbedCreator.create_embed(
                title="❌ Failed to Initialize Ranks",
                description=f"An error occurred: {e}",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)

    async def rank_create_command(
        self,
        ctx: commands.Context[Tux],
        rank: int,
        name: str,
        description: str | None = None,
    ) -> None:
        """Create a custom permission rank."""
        assert ctx.guild

        await ctx.defer()

        if not 0 <= rank <= 100:
            embed = EmbedCreator.create_embed(
                title="❌ Invalid Rank",
                description="Rank must be between 0 and 100.",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)
            return

        try:
            # Check if rank already exists
            existing = await self.bot.db.permission_ranks.get_permission_rank(ctx.guild.id, rank)
            if existing:
                embed = EmbedCreator.create_embed(
                    title="❌ Rank Already Exists",
                    description=f"Rank {rank} already exists: **{existing.name}**",
                    embed_type=EmbedType.ERROR,
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

            embed = EmbedCreator.create_embed(
                title="✅ Permission Rank Created",
                description=f"Created rank **{rank}**: **{name}**\n\nUse `/config role assign {rank} @Role` to assign roles to this rank.",
                embed_type=EmbedType.SUCCESS,
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = EmbedCreator.create_embed(
                title="❌ Failed to Create Rank",
                description=f"An error occurred: {e}",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)

    async def rank_delete_command(self, ctx: commands.Context[Tux], rank: int) -> None:
        """Delete a custom permission rank."""
        assert ctx.guild

        await ctx.defer()

        if rank <= 7:
            embed = EmbedCreator.create_embed(
                title="❌ Cannot Delete Default Rank",
                description="Ranks 0-7 are default ranks and cannot be deleted.\n\nUse `/config rank create` to add custom ranks (8-100).",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)
            return

        try:
            # Check if rank exists
            existing = await self.bot.db.permission_ranks.get_permission_rank(ctx.guild.id, rank)
            if not existing:
                embed = EmbedCreator.create_embed(
                    title="❌ Rank Not Found",
                    description=f"Rank {rank} does not exist.",
                    embed_type=EmbedType.ERROR,
                )
                await ctx.send(embed=embed)
                return

            # Delete the rank
            await self.bot.db.permission_ranks.delete_permission_rank(ctx.guild.id, rank)

            embed = EmbedCreator.create_embed(
                title="✅ Permission Rank Deleted",
                description=f"Deleted rank **{rank}**: **{existing.name}**",
                embed_type=EmbedType.SUCCESS,
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = EmbedCreator.create_embed(
                title="❌ Failed to Delete Rank",
                description=f"An error occurred: {e}",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)

    async def role_list_command(self, ctx: commands.Context[Tux]) -> None:
        """View all role-to-rank assignments."""
        assert ctx.guild

        await ctx.defer()

        assignments = await self.bot.db.permission_assignments.get_assignments_by_guild(ctx.guild.id)

        if not assignments:
            embed = EmbedCreator.create_embed(
                title="❌ No Role Assignments",
                description="No roles have been assigned to permission ranks.\n\nUse `/config role assign <rank> @Role` to assign roles.",
                embed_type=EmbedType.ERROR,
                custom_color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        embed = EmbedCreator.create_embed(
            title=f"👥 Role Assignments - {ctx.guild.name}",
            description=f"Total: {len(assignments)} role assignments",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
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

    async def role_assign_command(self, ctx: commands.Context[Tux], rank: int, role: discord.Role) -> None:
        """Assign permission rank to Discord role."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if rank exists
            rank_obj = await self.bot.db.permission_ranks.get_permission_rank(ctx.guild.id, rank)
            if not rank_obj:
                embed = EmbedCreator.create_embed(
                    title="❌ Rank Not Found",
                    description=f"Permission rank {rank} does not exist.\n\nUse `/config rank list` to see available ranks.",
                    embed_type=EmbedType.ERROR,
                )
                await ctx.send(embed=embed)
                return

            # Check if role is already assigned to this rank
            existing = await self.bot.db.permission_assignments.find_one(
                filters=(PermissionAssignment.guild_id == ctx.guild.id) & (PermissionAssignment.role_id == role.id),
            )
            if existing and existing.permission_rank_id == rank:
                embed = EmbedCreator.create_embed(
                    title="⚠️ Already Assigned",
                    description=f"Role {role.mention} is already assigned to rank {rank} (**{rank_obj.name}**).",
                    embed_type=EmbedType.WARNING,
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
                assigned_by=ctx.author.id,
            )

            embed = EmbedCreator.create_embed(
                title="✅ Role Assigned",
                description=f"Role {role.mention} has been assigned to rank **{rank}** (**{rank_obj.name}**).",
                embed_type=EmbedType.SUCCESS,
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = EmbedCreator.create_embed(
                title="❌ Failed to Assign Role",
                description=f"An error occurred: {e}",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)

    async def role_unassign_command(self, ctx: commands.Context[Tux], role: discord.Role) -> None:
        """Remove permission rank from role."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if role has an assignment
            assignment = await self.bot.db.permission_assignments.find_one(
                filters=(PermissionAssignment.guild_id == ctx.guild.id) & (PermissionAssignment.role_id == role.id),
            )
            if not assignment:
                embed = EmbedCreator.create_embed(
                    title="❌ No Assignment Found",
                    description=f"Role {role.mention} is not assigned to any permission rank.",
                    embed_type=EmbedType.ERROR,
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

            embed = EmbedCreator.create_embed(
                title="✅ Role Unassigned",
                description=f"Role {role.mention} has been removed from rank **{assignment.permission_rank_id}** (**{rank_name}**).",
                embed_type=EmbedType.SUCCESS,
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = EmbedCreator.create_embed(
                title="❌ Failed to Unassign Role",
                description=f"An error occurred: {e}",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)

    async def command_list_command(self, ctx: commands.Context[Tux]) -> None:
        """View all command permission requirements."""
        assert ctx.guild

        await ctx.defer()

        permissions = await self.bot.db.command_permissions.get_all_command_permissions(ctx.guild.id)

        if not permissions:
            embed = EmbedCreator.create_embed(
                title="📌 No Command Permissions",
                description="No commands have custom permission requirements.\n\nUse `/config command assign <command> <rank>` to set requirements.",
                embed_type=EmbedType.INFO,
            )
            await ctx.send(embed=embed)
            return

        embed = EmbedCreator.create_embed(
            title=f"🔒 Command Permissions - {ctx.guild.name}",
            description=f"Total: {len(permissions)} commands with custom permissions",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
        )

        # Group by category
        by_category: dict[str, list[str]] = {}
        for perm in permissions:
            category = perm.category or "General"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(f"`{perm.command_name}` → Rank {perm.required_rank}")

        for category in sorted(by_category.keys()):
            commands = by_category[category]
            embed.add_field(
                name=f"📁 {category}",
                value="\n".join(commands),
                inline=False,
            )

        embed.set_footer(text="Use /config command assign | unassign to manage permissions")
        await ctx.send(embed=embed)

    async def command_assign_command(
        self,
        ctx: commands.Context[Tux],
        command_name: str,
        rank: int,
        category: str | None = None,
    ) -> None:
        """Set permission rank requirement for command."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if rank exists
            rank_obj = await self.bot.db.permission_ranks.get_permission_rank(ctx.guild.id, rank)
            if not rank_obj:
                embed = EmbedCreator.create_embed(
                    title="❌ Rank Not Found",
                    description=f"Permission rank {rank} does not exist.\n\nUse `/config rank list` to see available ranks.",
                    embed_type=EmbedType.ERROR,
                )
                await ctx.send(embed=embed)
                return

            # Check if command permission already exists
            existing = await self.bot.db.command_permissions.get_command_permission(ctx.guild.id, command_name)
            if existing:
                embed = EmbedCreator.create_embed(
                    title="⚠️ Command Already Restricted",
                    description=f"Command `{command_name}` already requires rank **{existing.required_rank}**.\n\nUse `/config command unassign {command_name}` to remove the restriction first.",
                    embed_type=EmbedType.WARNING,
                )
                await ctx.send(embed=embed)
                return

            # Create command permission
            await self.bot.db.command_permissions.set_command_permission(
                guild_id=ctx.guild.id,
                command_name=command_name,
                required_rank=rank,
                category=category,
            )

            embed = EmbedCreator.create_embed(
                title="✅ Command Permission Set",
                description=f"Command `{command_name}` now requires rank **{rank}** (**{rank_obj.name}**).",
                embed_type=EmbedType.SUCCESS,
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = EmbedCreator.create_embed(
                title="❌ Failed to Set Command Permission",
                description=f"An error occurred: {e}",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)

    async def command_unassign_command(self, ctx: commands.Context[Tux], command_name: str) -> None:
        """Remove permission requirement from command."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if command permission exists
            existing = await self.bot.db.command_permissions.get_command_permission(ctx.guild.id, command_name)
            if not existing:
                embed = EmbedCreator.create_embed(
                    title="❌ No Permission Found",
                    description=f"Command `{command_name}` has no custom permission requirements.",
                    embed_type=EmbedType.ERROR,
                )
                await ctx.send(embed=embed)
                return

            # Remove command permission
            await self.bot.db.command_permissions.delete_where(
                filters=(PermissionCommand.guild_id == ctx.guild.id) & (PermissionCommand.command_name == command_name),
            )

            embed = EmbedCreator.create_embed(
                title="✅ Command Permission Removed",
                description=f"Command `{command_name}` no longer has custom permission requirements.",
                embed_type=EmbedType.SUCCESS,
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed = EmbedCreator.create_embed(
                title="❌ Failed to Remove Command Permission",
                description=f"An error occurred: {e}",
                embed_type=EmbedType.ERROR,
            )
            await ctx.send(embed=embed)
