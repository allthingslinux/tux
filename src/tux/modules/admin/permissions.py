"""
Permission Management Commands

This module provides comprehensive commands for server administrators to configure
their permission system. It supports:

- Creating and managing custom permission levels
- Assigning permission levels to Discord roles
- Setting command-specific permission requirements
- Managing blacklists and whitelists
- Bulk configuration operations
- Configuration export/import for self-hosting

All commands require administrator permissions or higher.
"""

import io
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.permission_system import get_permission_system
from tux.database.models.models import GuildCommandPermission, GuildPermissionAssignment, GuildPermissionLevel


class PermissionCommands(commands.Cog):
    """Permission management commands for server administrators."""

    def __init__(self, bot: Tux):
        self.bot = bot
        self.permission_system = get_permission_system()

    @commands.group(name="permission", aliases=["perm", "perms"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def permission_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage server permission system."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🔐 Permission System",
                description="Configure your server's permission hierarchy",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Quick Setup",
                value="`/permission setup` - Initialize default permission levels",
                inline=False,
            )
            embed.add_field(
                name="Level Management",
                value="`/permission level create` - Create custom levels\n"
                "`/permission level list` - View all levels\n"
                "`/permission level delete` - Remove levels",
                inline=False,
            )
            embed.add_field(
                name="Role Assignment",
                value="`/permission assign` - Assign levels to roles\n"
                "`/permission unassign` - Remove role assignments\n"
                "`/permission assignments` - View current assignments",
                inline=False,
            )
            embed.add_field(
                name="Command Permissions",
                value="`/permission command set` - Set command requirements\n"
                "`/permission command list` - View command permissions\n"
                "`/permission command clear` - Remove command restrictions",
                inline=False,
            )
            await ctx.send(embed=embed)

    @permission_group.command(name="setup")
    async def setup_permissions(self, ctx: commands.Context[Tux]) -> None:
        # sourcery skip: merge-assign-and-aug-assign
        """Initialize default permission levels for your server."""
        if not ctx.guild:
            return

        embed = discord.Embed(
            title="🔧 Permission Setup",
            description="Setting up default permission levels...",
            color=discord.Color.blue(),
        )
        setup_msg = await ctx.send(embed=embed)

        try:
            # Initialize default levels
            await self.permission_system.initialize_guild(ctx.guild.id)

            embed.description = "✅ Default permission levels created!\n\n"
            embed.description += "**Default Levels:**\n"
            embed.description += "• 0: Member - Basic server access\n"
            embed.description += "• 1: Helper - Can help users\n"
            embed.description += "• 2: Trial Mod - Moderation training\n"
            embed.description += "• 3: Moderator - Can kick/ban/timeout\n"
            embed.description += "• 4: Senior Mod - Can unban/manage others\n"
            embed.description += "• 5: Administrator - Server administration\n"
            embed.description += "• 6: Head Admin - Full server control\n"
            embed.description += "• 7: Server Owner - Complete access\n\n"
            embed.description += "**Next Steps:**\n"
            embed.description += "• Use `/permission assign` to assign these levels to your roles\n"
            embed.description += "• Use `/permission level create` to add custom levels\n"
            embed.description += "• Use `/permission command set` to customize command permissions"

            embed.color = discord.Color.green()
            await setup_msg.edit(embed=embed)

        except Exception as e:
            embed.description = f"❌ Failed to setup permissions: {e}"
            embed.color = discord.Color.red()
            await setup_msg.edit(embed=embed)

    @permission_group.group(name="level")
    async def level_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage permission levels."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @level_group.command(name="create")
    @app_commands.describe(
        level="Permission level number (0-100)",
        name="Display name for this level",
        description="Optional description",
        color="Optional hex color (e.g., #FF0000)",
    )
    async def create_level(
        self,
        ctx: commands.Context[Tux],
        level: int,
        name: str,
        description: str | None = None,
        color: str | None = None,
    ) -> None:
        """Create a custom permission level."""
        if not ctx.guild:
            return

        if level < 0 or level > 100:
            await ctx.send("❌ Permission level must be between 0 and 100.")
            return

        # Parse color if provided
        color_int = None
        if color:
            try:
                color_int = int(color[1:], 16) if color.startswith("#") else int(color, 16)
            except ValueError:
                await ctx.send("❌ Invalid color format. Use hex format like #FF0000.")
                return

        try:
            await self.permission_system.create_custom_permission_level(
                guild_id=ctx.guild.id,
                level=level,
                name=name,
                description=description,
                color=color_int,
            )

            embed = discord.Embed(title="✅ Permission Level Created", color=color_int or discord.Color.green())
            embed.add_field(name="Level", value=str(level), inline=True)
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Description", value=description or "None", inline=True)
            if color_int:
                embed.add_field(name="Color", value=f"#{color_int:06X}", inline=True)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to create permission level: {e}")

    @level_group.command(name="list")
    async def list_levels(self, ctx: commands.Context[Tux]) -> None:
        """List all permission levels for this server."""
        if not ctx.guild:
            return

        try:
            levels = await self.permission_system.get_guild_permission_levels(ctx.guild.id)

            if not levels:
                await ctx.send("❌ No permission levels configured. Use `/permission setup` to initialize defaults.")
                return

            embed = discord.Embed(
                title="🔐 Permission Levels",
                description=f"Configured levels for {ctx.guild.name}",
                color=discord.Color.blue(),
            )

            for level in sorted(levels, key=lambda level: level.position):
                level_name = level.name
                if level.color:
                    level_name = f"[{level_name}](color:{level.color})"

                embed.add_field(
                    name=f"Level {level.level}: {level_name}",
                    value=level.description or "No description",
                    inline=False,
                )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to list permission levels: {e}")

    @level_group.command(name="delete")
    @app_commands.describe(level="Permission level to delete")
    async def delete_level(self, ctx: commands.Context[Tux], level: int) -> None:
        """Delete a custom permission level."""
        if not ctx.guild:
            return

        try:
            # Check if level exists and is custom (not default)
            existing = await self.permission_system.db.guild_permissions.get_permission_level(ctx.guild.id, level)

            if not existing:
                await ctx.send("❌ Permission level not found.")
                return

            # Prevent deletion of default levels
            if level in {0, 1, 2, 3, 4, 5, 6, 7}:
                await ctx.send("❌ Cannot delete default permission levels (0-7).")
                return

            # Confirm deletion
            embed = discord.Embed(
                title="⚠️ Confirm Deletion",
                description=f"Are you sure you want to delete permission level {level} ({existing.name})?",
                color=discord.Color.orange(),
            )

            view = ConfirmView(ctx.author)
            confirm_msg = await ctx.send(embed=embed, view=view)
            await view.wait()

            if not view.confirmed:
                await confirm_msg.edit(content="❌ Deletion cancelled.", embed=None, view=None)
                return

            # Delete the level
            deleted = await self.permission_system.db.guild_permissions.delete_permission_level(ctx.guild.id, level)

            if deleted:
                await confirm_msg.edit(
                    content=f"✅ Deleted permission level {level} ({existing.name}).",
                    embed=None,
                    view=None,
                )
            else:
                await confirm_msg.edit(content="❌ Failed to delete permission level.", embed=None, view=None)

        except Exception as e:
            await ctx.send(f"❌ Failed to delete permission level: {e}")

    @permission_group.command(name="assign")
    @app_commands.describe(level="Permission level to assign", role="Discord role to assign the level to")
    async def assign_level(self, ctx: commands.Context[Tux], level: int, role: discord.Role) -> None:
        """Assign a permission level to a Discord role."""
        if not ctx.guild:
            return

        try:
            await self.permission_system.assign_permission_level(
                guild_id=ctx.guild.id,
                level=level,
                role_id=role.id,
                assigned_by=ctx.author.id,
            )

            embed = discord.Embed(title="✅ Permission Level Assigned", color=discord.Color.green())
            embed.add_field(name="Level", value=str(level), inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            embed.add_field(name="Assigned By", value=ctx.author.mention, inline=True)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to assign permission level: {e}")

    @permission_group.command(name="unassign")
    @app_commands.describe(role="Discord role to remove assignment from")
    async def unassign_level(self, ctx: commands.Context[Tux], role: discord.Role) -> None:
        """Remove a permission level assignment from a role."""
        if not ctx.guild:
            return

        try:
            removed = await self.permission_system.db.permission_assignments.remove_role_assignment(
                ctx.guild.id,
                role.id,
            )

            if removed:
                embed = discord.Embed(
                    title="✅ Permission Assignment Removed",
                    description=f"Removed permission assignment from {role.mention}",
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ No permission assignment found for {role.mention}.")

        except Exception as e:
            await ctx.send(f"❌ Failed to remove permission assignment: {e}")

    @permission_group.command(name="assignments")
    async def list_assignments(self, ctx: commands.Context[Tux]) -> None:
        """List all permission level assignments for this server."""
        if not ctx.guild:
            return

        try:
            assignments = await self.permission_system.get_guild_assignments(ctx.guild.id)

            if not assignments:
                await ctx.send("❌ No permission assignments configured.")
                return

            embed = discord.Embed(
                title="🔗 Permission Assignments",
                description=f"Role assignments for {ctx.guild.name}",
                color=discord.Color.blue(),
            )

            # Group assignments by level
            level_assignments: dict[int, list[tuple[GuildPermissionAssignment, GuildPermissionLevel]]] = {}
            for assignment in assignments:
                level_info_opt = await self.permission_system.db.guild_permissions.get_permission_level(
                    ctx.guild.id,
                    assignment.permission_level_id,
                )
                if level_info_opt is not None:
                    level_info = level_info_opt
                    level: int = level_info.level
                    if level not in level_assignments:
                        level_assignments[level] = []
                    level_assignments[level].append((assignment, level_info))

            for level in sorted(level_assignments.keys()):
                assignments_info = level_assignments[level]
                assignment: GuildPermissionAssignment = assignments_info[0][0]
                level_info: GuildPermissionLevel = assignments_info[0][1]

                role_mentions: list[str] = []
                for assign, _ in assignments_info:
                    assign: GuildPermissionAssignment
                    if role := ctx.guild.get_role(assign.role_id):
                        role_mentions.append(role.mention)

                if role_mentions:
                    embed.add_field(
                        name=f"Level {level}: {level_info.name}",
                        value=", ".join(role_mentions),
                        inline=False,
                    )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to list assignments: {e}")

    @permission_group.group(name="command")
    async def command_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage command-specific permissions."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @command_group.command(name="set")
    @app_commands.describe(
        command="Command name (without prefix)",
        level="Required permission level",
        category="Optional category for organization",
    )
    async def set_command_permission(
        self,
        ctx: commands.Context[Tux],
        command: str,
        level: int,
        category: str | None = None,
    ) -> None:
        """Set permission level required for a specific command."""
        if not ctx.guild:
            return

        if level < 0 or level > 100:
            await ctx.send("❌ Permission level must be between 0 and 100.")
            return

        try:
            await self.permission_system.set_command_permission(
                guild_id=ctx.guild.id,
                command_name=command,
                required_level=level,
                category=category,
            )

            embed = discord.Embed(title="✅ Command Permission Set", color=discord.Color.green())
            embed.add_field(name="Command", value=f"`{command}`", inline=True)
            embed.add_field(name="Required Level", value=str(level), inline=True)
            if category:
                embed.add_field(name="Category", value=category, inline=True)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to set command permission: {e}")

    @command_group.command(name="list")
    async def list_command_permissions(self, ctx: commands.Context[Tux]) -> None:
        """List all command-specific permission requirements."""
        if not ctx.guild:
            return

        try:
            cmd_perms = await self.permission_system.get_guild_command_permissions(ctx.guild.id)

            if not cmd_perms:
                await ctx.send("❌ No command-specific permissions configured.")
                return

            embed = discord.Embed(
                title="📋 Command Permissions",
                description=f"Custom permissions for {ctx.guild.name}",
                color=discord.Color.blue(),
            )

            # Group by category
            categorized: dict[str, list[GuildCommandPermission]] = {}
            uncategorized: list[GuildCommandPermission] = []

            for cmd_perm in cmd_perms:
                if cmd_perm.category:
                    if cmd_perm.category not in categorized:
                        categorized[cmd_perm.category] = []
                    categorized[cmd_perm.category].append(cmd_perm)
                else:
                    uncategorized.append(cmd_perm)

            # Add categorized commands
            for category, commands in categorized.items():
                cmd_list = [f"`{cmd.command_name}` (Level {cmd.required_level})" for cmd in commands]
                embed.add_field(name=f"📁 {category.title()}", value="\n".join(cmd_list), inline=False)

            # Add uncategorized commands
            if uncategorized:
                cmd_list = [f"`{cmd.command_name}` (Level {cmd.required_level})" for cmd in uncategorized]
                embed.add_field(name="📄 Other Commands", value="\n".join(cmd_list), inline=False)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to list command permissions: {e}")

    @permission_group.group(name="blacklist")
    async def blacklist_group(self, ctx: commands.Context[Tux]) -> None:
        """Manage user/channel/role blacklists."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @blacklist_group.command(name="user")
    @app_commands.describe(
        user="User to blacklist",
        reason="Reason for blacklisting",
        duration="Duration (e.g., 1d, 1h, 30m)",
    )
    async def blacklist_user(
        self,
        ctx: commands.Context[Tux],
        user: discord.Member,
        reason: str | None = None,
        duration: str | None = None,
    ) -> None:
        """Blacklist a user from using commands."""
        if not ctx.guild:
            return

        # Parse duration
        expires_at = None
        if duration:
            try:
                # Simple duration parsing (e.g., "1d", "2h", "30m")
                if duration.endswith("d"):
                    days = int(duration[:-1])
                    expires_at = datetime.now(UTC) + timedelta(days=days)
                elif duration.endswith("h"):
                    hours = int(duration[:-1])
                    expires_at = datetime.now(UTC) + timedelta(hours=hours)
                elif duration.endswith("m"):
                    minutes = int(duration[:-1])
                    expires_at = datetime.now(UTC) + timedelta(minutes=minutes)
                else:
                    await ctx.send("❌ Invalid duration format. Use formats like: 1d, 2h, 30m")
                    return
            except ValueError:
                await ctx.send("❌ Invalid duration format.")
                return

        try:
            await self.permission_system.blacklist_user(
                guild_id=ctx.guild.id,
                user_id=user.id,
                blacklisted_by=ctx.author.id,
                reason=reason,
                expires_at=expires_at,
            )

            embed = discord.Embed(title="🚫 User Blacklisted", color=discord.Color.red())
            embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Blacklisted By", value=ctx.author.mention, inline=True)
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            if expires_at:
                embed.add_field(name="Expires", value=f"<t:{int(expires_at.timestamp())}:R>", inline=True)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to blacklist user: {e}")

    @blacklist_group.command(name="remove")
    @app_commands.describe(target="User, role, or channel to unblacklist")
    async def unblacklist(
        self,
        ctx: commands.Context[Tux],
        target: discord.Member | discord.Role | discord.TextChannel,
    ) -> None:
        """Remove a user/role/channel from the blacklist."""
        if not ctx.guild:
            return

        # Determine target type
        if isinstance(target, discord.Member):
            target_type = "user"
        elif isinstance(target, discord.Role):
            target_type = "role"
        else:
            # In guild context, channels are always TextChannel
            target_type = "channel"

        try:
            removed = await self.permission_system.db.guild_blacklist.remove_from_blacklist(
                ctx.guild.id,
                target_type,
                target.id,
            )

            if removed:
                embed = discord.Embed(
                    title="✅ Blacklist Removed",
                    description=f"Removed {target.mention} from blacklist",
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ {target.mention} is not blacklisted.")

        except Exception as e:
            await ctx.send(f"❌ Failed to remove from blacklist: {e}")

    @permission_group.command(name="export")
    async def export_config(self, ctx: commands.Context[Tux]) -> None:
        """Export permission configuration as JSON for backup/sharing."""
        if not ctx.guild:
            return

        try:
            # Gather all configuration data
            config: dict[str, int | str | list[dict[str, Any]]] = {
                "guild_id": ctx.guild.id,
                "guild_name": ctx.guild.name,
                "exported_at": datetime.now(UTC).isoformat(),
                "exported_by": ctx.author.id,
                "permission_levels": [],
                "role_assignments": [],
                "command_permissions": [],
                "blacklists": [],
                "whitelists": [],
            }

            # Get permission levels
            levels = await self.permission_system.get_guild_permission_levels(ctx.guild.id)
            permission_levels_list = config["permission_levels"]
            assert isinstance(permission_levels_list, list)
            for level in levels:
                permission_levels_list.append(
                    {
                        "level": level.level,
                        "name": level.name,
                        "description": level.description,
                        "color": level.color,
                        "position": level.position,
                        "enabled": level.enabled,
                    },
                )

            # Get role assignments
            assignments = await self.permission_system.get_guild_assignments(ctx.guild.id)
            role_assignments_list = config["role_assignments"]
            assert isinstance(role_assignments_list, list)
            for assignment in assignments:
                level_info = await self.permission_system.db.guild_permissions.get_permission_level(
                    ctx.guild.id,
                    assignment.permission_level_id,
                )
                if level_info:
                    role_assignments_list.append(
                        {
                            "level": level_info.level,
                            "role_id": assignment.role_id,
                            "assigned_by": assignment.assigned_by,
                            "assigned_at": assignment.assigned_at.isoformat(),
                        },
                    )

            # Get command permissions
            cmd_perms = await self.permission_system.get_guild_command_permissions(ctx.guild.id)
            command_permissions_list = config["command_permissions"]
            assert isinstance(command_permissions_list, list)
            for cmd_perm in cmd_perms:
                command_permissions_list.append(
                    {
                        "command_name": cmd_perm.command_name,
                        "required_level": cmd_perm.required_level,
                        "category": cmd_perm.category,
                        "description": cmd_perm.description,
                        "enabled": cmd_perm.enabled,
                    },
                )

            # Convert to JSON and send as file
            json_data = json.dumps(config, indent=2)
            file = discord.File(
                io.BytesIO(json_data.encode("utf-8")),
                filename=f"{ctx.guild.name}_permissions_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json",
            )

            embed = discord.Embed(
                title="📤 Permission Config Exported",
                description="Configuration file contains all your permission settings.",
                color=discord.Color.green(),
            )

            await ctx.send(embed=embed, file=file)

        except Exception as e:
            await ctx.send(f"❌ Failed to export configuration: {e}")


class ConfirmView(discord.ui.View):
    """Confirmation dialog for destructive actions."""

    def __init__(self, author: discord.User | discord.Member):
        super().__init__(timeout=60)
        self.author = author
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Get the user ID regardless of whether author is User or Member
        if isinstance(self.author, discord.User):
            author_id = self.author.id
        else:
            # For Member objects, access the underlying user
            author_id = getattr(self.author, "user", self.author).id
        return interaction.user.id == author_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        self.confirmed = True
        await interaction.response.edit_message(content="✅ Confirmed!", view=None)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        self.confirmed = False
        await interaction.response.edit_message(content="❌ Cancelled.", view=None)
        self.stop()

    async def on_timeout(self):
        self.confirmed = False


async def setup(bot: Tux) -> None:
    """Set up the PermissionCommands cog."""
    await bot.add_cog(PermissionCommands(bot))
