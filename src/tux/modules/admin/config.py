"""
Guild Configuration Management

A comprehensive system for configuring all aspects of guild operation including
permission ranks, logging, channels, roles, and command access control.

Note: "Ranks" (permission hierarchy) are distinct from "Levels" (XP system).

Command Structure:
==================

/config [overview]
├── Show complete guild configuration overview
├── Displays: prefix, ranks, role assignments, log channels, co2mmand permissions
└── Usage: /config

/config rank <subcommand>
├── init           - Initialize default permission ranks (0-7)
├── create         - Create custom permission rank
│   └── Args: rank:int, name:str, description:str?
├── delete         - Delete custom permission rank
│   └── Args: rank:int
├── list           - View all permission ranks
└── [fallback]     - Same as 'list' if no subcommand

/config role <subcommand>
├── assign         - Assign permission rank to Discord role
│   └── Args: rank:int, role:Role
├── unassign       - Remove permission rank from role
│   └── Args: role:Role
└── list           - View all role-to-rank assignments

/config command <subcommand>
├── assign         - Set permission rank requirement for command
│   └── Args: command_name:str, rank:int, category:str?
├── unassign       - Remove permission requirement from command
│   └── Args: command_name:str
└── list           - View all command permission requirements

Examples:
---------
/config rank init                          # Initialize defaults
/config rank create 10 "VIP" "VIP perks"   # Custom rank
/config rank delete 10                     # Delete custom rank
/config role assign 3 @Moderator           # Mod rank to role
/config command assign ban 3               # Require rank 3 for ban
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.checks import requires_command_permission
from tux.core.permission_system import get_permission_system
from tux.ui.embeds import EmbedCreator, EmbedType

if TYPE_CHECKING:
    from tux.core.bot import Tux


class Config(BaseCog):
    """
    Guild configuration management with hybrid commands.

    This cog provides a complete interface for server administrators to configure:
    - Dynamic permission ranks and role assignments
    - Command-specific permission requirements
    - Log channels for various events
    - Functional channels (jail, general, etc.)
    - Special roles and bot prefix

    Terminology:
    - **Rank** = Permission tier (0-100) for access control
    - **Rank** = XP/activity system (separate feature)
    """

    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.permission_system = get_permission_system()

    # ========== MAIN GROUP & OVERVIEW ==========

    @commands.hybrid_group(name="config", fallback="overview")
    @commands.guild_only()
    @requires_command_permission()
    async def config(self, ctx: commands.Context[Tux]) -> None:  # noqa: PLR0912
        # sourcery skip: low-code-quality
        """
        View complete guild configuration overview.

        Shows summary of all configured settings including permissions,
        log channels, roles, and command restrictions.
        """
        assert ctx.guild

        await ctx.defer()

        # Fetch all configuration data
        guild_config = await self.db.guild_config.get_config_by_guild_id(ctx.guild.id)
        permission_ranks = await self.db.guild_permissions.get_permission_ranks_by_guild(ctx.guild.id)
        assignments = await self.db.permission_assignments.get_assignments_by_guild(ctx.guild.id)
        command_perms = await self.db.command_permissions.get_all_command_permissions(ctx.guild.id)

        # Build overview embed
        embed = EmbedCreator.create_embed(
            title=f"⚙️ Guild Configuration - {ctx.guild.name}",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
        )

        # Basic info
        prefix = guild_config.prefix if guild_config else "$"
        embed.add_field(name="🔧 Prefix", value=f"`{prefix}`", inline=True)
        embed.add_field(name="📊 Permission Ranks", value=str(len(permission_ranks)), inline=True)
        embed.add_field(name="🔗 Role Assignments", value=str(len(assignments)), inline=True)

        # Log channels section
        if guild_config:
            log_channels: list[str] = []
            if guild_config.mod_log_id:
                log_channels.append(f"**Mod:** <#{guild_config.mod_log_id}>")
            if guild_config.audit_log_id:
                log_channels.append(f"**Audit:** <#{guild_config.audit_log_id}>")
            if guild_config.join_log_id:
                log_channels.append(f"**Join:** <#{guild_config.join_log_id}>")
            if guild_config.private_log_id:
                log_channels.append(f"**Private:** <#{guild_config.private_log_id}>")

            if log_channels:
                embed.add_field(name="📝 Log Channels", value="\n".join(log_channels), inline=False)

            # Functional channels
            func_channels: list[str] = []
            if guild_config.jail_channel_id:
                func_channels.append(f"**Jail:** <#{guild_config.jail_channel_id}>")
            if guild_config.general_channel_id:
                func_channels.append(f"**General:** <#{guild_config.general_channel_id}>")

            if func_channels:
                embed.add_field(name="🏛️ Functional Channels", value="\n".join(func_channels), inline=False)

        # Permission ranks preview
        if permission_ranks:
            ranks_preview = "\n".join(
                f"`Rank {pl.rank}` {pl.name}" for pl in sorted(permission_ranks, key=lambda x: x.rank)[:5]
            )
            if len(permission_ranks) > 5:
                ranks_preview += f"\n*+{len(permission_ranks) - 5} more ranks*"
            embed.add_field(name="🎯 Permission Ranks", value=ranks_preview, inline=False)

        # Command permissions preview
        if command_perms:
            cmd_preview = "\n".join(f"`{cmd.command_name}` → Rank {cmd.required_rank}" for cmd in command_perms[:5])
            if len(command_perms) > 5:
                cmd_preview += f"\n*+{len(command_perms) - 5} more commands*"
            embed.add_field(name="🛡️ Command Permissions", value=cmd_preview, inline=False)

        embed.set_footer(text="Use /config <subcommand> to modify settings")

        await ctx.send(embed=embed)

    # ========== PERMISSION RANKS ==========

    @config.group(name="rank", fallback="list")
    @commands.guild_only()
    async def rank(self, ctx: commands.Context[Tux]) -> None:
        """
        List all permission ranks in this guild.

        Permission ranks define a hierarchy from 0-100 that can be assigned
        to roles and used to control command access.
        """
        assert ctx.guild

        await ctx.defer()

        ranks = await self.db.guild_permissions.get_permission_ranks_by_guild(ctx.guild.id)

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

        for rank in sorted(ranks, key=lambda x: x.rank):
            status_icon = "✅" if rank.enabled else "❌"
            level_title = f"{status_icon} Rank {rank.rank}: {rank.name}"

            desc_parts = [rank.description or "*No description*"]
            if rank.color:
                desc_parts.append(f"Color: `#{rank.color:06X}`")

            embed.add_field(
                name=level_title,
                value=" | ".join(desc_parts),
                inline=False,
            )

        await ctx.send(embed=embed)

    @rank.command(name="init")
    @commands.guild_only()
    async def rank_init(self, ctx: commands.Context[Tux]) -> None:
        """
        Initialize default permission ranks.

        Creates a standard 8-rank hierarchy (0-7) from Member to Server Owner.
        Safe to run multiple times - won't duplicate existing ranks.
        """
        assert ctx.guild

        await ctx.defer()

        try:
            await self.permission_system.initialize_guild(ctx.guild.id)

            embed = EmbedCreator.create_embed(
                title="✅ Permission System Initialized",
                description=(
                    "Default permission ranks created successfully!\n\n"
                    "**Standard Hierarchy:**\n"
                    "🔹 **Rank 0:** Member - Basic access\n"
                    "🔹 **Rank 1:** Trusted - Helper role\n"
                    "🔹 **Rank 2:** Junior Moderator - Training\n"
                    "🔹 **Rank 3:** Moderator - Full moderation\n"
                    "🔹 **Rank 4:** Senior Moderator - Advanced mod\n"
                    "🔹 **Rank 5:** Administrator - Server admin\n"
                    "🔹 **Rank 6:** Head Administrator - Full control\n"
                    "🔹 **Rank 7:** Server Owner - Complete access\n\n"
                    "**Next Steps:**\n"
                    "• Use `/config role assign <rank> <role>` to assign ranks to roles\n"
                    "• Use `/config command assign <command> <rank>` to protect commands"
                ),
                embed_type=EmbedType.SUCCESS,
                custom_color=discord.Color.green(),
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to initialize permission ranks: {e}")

    @rank.command(name="create")
    @commands.guild_only()
    async def rank_create(
        self,
        ctx: commands.Context[Tux],
        rank: int,
        name: str,
        description: str | None = None,
    ) -> None:
        """
        Create a custom permission rank.

        Allows you to define custom permission tiers beyond the standard 0-7.
        Useful for specialized roles or fine-grained access control.
        """
        assert ctx.guild

        if not 0 <= rank <= 100:
            await ctx.send("❌ Permission rank must be between 0 and 100.")
            return

        await ctx.defer()

        try:
            await self.permission_system.create_custom_permission_rank(
                guild_id=ctx.guild.id,
                rank=rank,
                name=name,
                description=description,
            )

            embed = EmbedCreator.create_embed(
                title="✅ Custom Permission Rank Created",
                description=(
                    f"**Rank:** {rank}\n"
                    f"**Name:** {name}\n"
                    f"**Description:** {description or '*None provided*'}\n\n"
                    f"Assign this rank to roles with:\n"
                    f"`/config role assign {rank} @role`"
                ),
                embed_type=EmbedType.SUCCESS,
                custom_color=discord.Color.green(),
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to create permission rank: {e}")

    @rank.command(name="delete")
    @commands.guild_only()
    async def rank_delete(
        self,
        ctx: commands.Context[Tux],
        rank: int,
    ) -> None:
        """
        Delete a custom permission rank.

        This will remove the rank and all associated role assignments.
        Built-in ranks (0-7) cannot be deleted.
        """
        assert ctx.guild

        if not 0 <= rank <= 100:
            await ctx.send("❌ Permission rank must be between 0 and 100.")
            return

        await ctx.defer()

        try:
            success = await self.db.guild_permissions.delete_permission_rank(
                guild_id=ctx.guild.id,
                rank=rank,
            )

            if success:
                embed = EmbedCreator.create_embed(
                    title="✅ Permission Rank Deleted",
                    description=(f"**Rank:** {rank}\n\nAll role assignments for this rank have been removed."),
                    embed_type=EmbedType.SUCCESS,
                    custom_color=discord.Color.green(),
                )
            else:
                embed = EmbedCreator.create_embed(
                    title="❌ Rank Not Found",
                    description=f"No permission rank **{rank}** exists in this guild.",
                    embed_type=EmbedType.ERROR,
                    custom_color=discord.Color.red(),
                )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to delete permission rank: {e}")

    # ========== ROLE ASSIGNMENTS ==========

    @config.group(name="role", fallback="list")
    @commands.guild_only()
    async def role(self, ctx: commands.Context[Tux]) -> None:
        """
        List all role → permission rank assignments.

        Shows which Discord roles are assigned to which permission ranks,
        determining what commands members with those roles can use.
        """
        assert ctx.guild

        await ctx.defer()

        assignments = await self.db.permission_assignments.get_assignments_by_guild(ctx.guild.id)

        if not assignments:
            embed = EmbedCreator.create_embed(
                title="❌ No Role Assignments",
                description=(
                    "No roles assigned to permission ranks.\n\n"
                    "Use `/config role assign <rank> <role>` to assign ranks to roles."
                ),
                embed_type=EmbedType.ERROR,
                custom_color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        embed = EmbedCreator.create_embed(
            title=f"🔗 Role Assignments - {ctx.guild.name}",
            description=f"Total: {len(assignments)} assignments",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
        )

        # Group by permission rank
        rank_map: dict[int, list[int]] = defaultdict(list)

        for assignment in assignments:
            rank_record = await self.db.guild_permissions.get_by_id(assignment.permission_rank_id)
            if rank_record:
                rank_map[rank_record.rank].append(assignment.role_id)

        # Display sorted by rank
        ranks = await self.db.guild_permissions.get_permission_ranks_by_guild(ctx.guild.id)

        for rank_num in sorted(rank_map.keys()):
            role_ids = rank_map[rank_num]
            role_mentions = [f"<@&{rid}>" for rid in role_ids]

            rank_name = next((pl.name for pl in ranks if pl.rank == rank_num), f"Rank {rank_num}")

            embed.add_field(
                name=f"Rank {rank_num}: {rank_name}",
                value=", ".join(role_mentions) if role_mentions else "*No roles*",
                inline=False,
            )

        await ctx.send(embed=embed)

    @role.command(name="assign")
    @commands.guild_only()
    async def role_assign(
        self,
        ctx: commands.Context[Tux],
        rank: int,
        role: discord.Role,
    ) -> None:
        """
        Assign a permission rank to a Discord role.

        Members with this role will gain access to commands requiring
        this permission rank or lower.
        """
        assert ctx.guild

        await ctx.defer()

        try:
            await self.permission_system.assign_permission_rank(
                guild_id=ctx.guild.id,
                rank=rank,
                role_id=role.id,
                assigned_by=ctx.author.id,
            )

            embed = EmbedCreator.create_embed(
                title="✅ Rank Assigned",
                description=(
                    f"**Rank:** {rank}\n"
                    f"**Role:** {role.mention}\n"
                    f"**Assigned by:** {ctx.author.mention}\n\n"
                    f"Members with {role.mention} can now use commands requiring rank {rank} or lower."
                ),
                embed_type=EmbedType.SUCCESS,
                custom_color=discord.Color.green(),
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to create assignment: {e}")

    @role.command(name="unassign")
    @commands.guild_only()
    async def role_unassign(
        self,
        ctx: commands.Context[Tux],
        role: discord.Role,
    ) -> None:
        """
        Unassign permission rank from a role.

        The role will no longer grant any permission rank.
        Members may still have permissions from other roles.
        """
        assert ctx.guild

        await ctx.defer()

        try:
            assignments = await self.db.permission_assignments.get_assignments_by_guild(ctx.guild.id)
            assignment = next((a for a in assignments if a.role_id == role.id), None)

            if not assignment:
                await ctx.send(f"❌ No assignment found for {role.mention}")
                return

            await self.db.permission_assignments.delete_by_id(assignment.id)

            embed = EmbedCreator.create_embed(
                title="✅ Rank Unassigned",
                description=f"Unassigned permission rank from {role.mention}",
                embed_type=EmbedType.SUCCESS,
                custom_color=discord.Color.green(),
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to unassign rank: {e}")

    # ========== COMMAND REQUIREMENTS ==========

    @config.group(name="command", fallback="list")
    @commands.guild_only()
    async def command(self, ctx: commands.Context[Tux]) -> None:
        """
        List all command permission requirements.

        Shows which commands require specific permission ranks to use.
        By default, commands are accessible to everyone unless assigned a requirement.
        """
        assert ctx.guild

        await ctx.defer()

        command_perms = await self.db.command_permissions.get_all_command_permissions(ctx.guild.id)

        if not command_perms:
            embed = EmbedCreator.create_embed(
                title="❌ No Command Requirements",
                description=(
                    "No command permission requirements assigned.\n\n"
                    "Commands are unrestricted by default.\n"
                    "Use `/config command assign <command> <rank>` to restrict commands."
                ),
                embed_type=EmbedType.ERROR,
                custom_color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        embed = EmbedCreator.create_embed(
            title=f"🛡️ Command Permissions - {ctx.guild.name}",
            description=f"Total: {len(command_perms)} commands configured",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
        )

        # Group by category
        categorized: dict[str | None, list[str]] = defaultdict(list)

        for cmd_perm in sorted(command_perms, key=lambda x: (x.category or "", x.command_name)):
            status = "✅" if cmd_perm.enabled else "❌"
            cmd_text = f"{status} `{cmd_perm.command_name}` → Rank {cmd_perm.required_rank}"
            categorized[cmd_perm.category].append(cmd_text)

        # Display by category
        for category, cmds in categorized.items():
            category_name = f"📁 {category.title()}" if category else "📄 Uncategorized"

            # Limit to 10 per field to avoid embed limits
            if len(cmds) <= 10:
                embed.add_field(name=category_name, value="\n".join(cmds), inline=False)
            else:
                embed.add_field(name=category_name, value="\n".join(cmds[:10]), inline=False)
                embed.add_field(name="", value=f"*+{len(cmds) - 10} more commands...*", inline=False)

        await ctx.send(embed=embed)

    @command.command(name="assign")
    @commands.guild_only()
    async def command_assign(
        self,
        ctx: commands.Context[Tux],
        command_name: str,
        rank: int,
        category: str | None = None,
    ) -> None:
        """
        Assign a permission rank requirement to a command.

        Only members with the specified permission rank (or higher)
        will be able to use this command.
        """
        assert ctx.guild

        if not 0 <= rank <= 100:
            await ctx.send("❌ Permission rank must be between 0 and 100.")
            return

        await ctx.defer()

        try:
            await self.permission_system.set_command_permission(
                guild_id=ctx.guild.id,
                command_name=command_name,
                required_rank=rank,
                category=category,
            )

            embed = EmbedCreator.create_embed(
                title="✅ Requirement Assigned",
                description=(
                    f"**Command:** `{command_name}`\n"
                    f"**Required Rank:** {rank}"
                    + (f"\n**Category:** {category}" if category else "")
                    + f"\n\nOnly users with permission rank {rank}+ can use this command."
                ),
                embed_type=EmbedType.SUCCESS,
                custom_color=discord.Color.green(),
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to assign requirement: {e}")

    @command.command(name="unassign")
    @commands.guild_only()
    async def command_unassign(
        self,
        ctx: commands.Context[Tux],
        command_name: str,
    ) -> None:
        """
        Unassign permission requirement from a command.

        The command will become accessible to all members again.
        """
        assert ctx.guild

        await ctx.defer()

        try:
            # Find and delete the command permission
            command_perms = await self.db.command_permissions.get_all_command_permissions(ctx.guild.id)
            cmd_perm = next((cp for cp in command_perms if cp.command_name == command_name), None)

            if not cmd_perm:
                await ctx.send(f"❌ No requirement configured for command `{command_name}`")
                return

            await self.db.command_permissions.delete_by_id(cmd_perm.id)

            embed = EmbedCreator.create_embed(
                title="✅ Requirement Unassigned",
                description=f"Command `{command_name}` is now unrestricted.",
                embed_type=EmbedType.SUCCESS,
                custom_color=discord.Color.green(),
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to unassign requirement: {e}")


async def setup(bot: Tux) -> None:
    """Load the Config cog."""
    await bot.add_cog(Config(bot))
