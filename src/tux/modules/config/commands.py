"""Command permission management for the config system."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from tux.database.models.models import PermissionCommand

from .base import BaseConfigManager

if TYPE_CHECKING:
    from tux.core.bot import Tux


class CommandManager(BaseConfigManager):
    """Management commands for command permissions."""

    async def configure_commands(self, ctx: commands.Context[Tux]) -> None:
        """
        Configure command permissions using the unified config dashboard.

        This command launches the unified configuration dashboard in commands mode
        to allow administrators to assign permission ranks to moderation commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command invocation.
        """
        await self.configure_dashboard(ctx, "commands")

    async def list_permissions(self, ctx: commands.Context[Tux]) -> None:
        """View all command permission requirements."""
        assert ctx.guild

        await ctx.defer()

        permissions = await self.bot.db.command_permissions.get_all_command_permissions(ctx.guild.id)

        if not permissions:
            embed = self.create_info_embed(
                "📌 No Command Permissions",
                "No commands have custom permission requirements.\n\nUse `/config commands assign <command> <rank>` to set requirements.",
            )
            await ctx.send(embed=embed)
            return

        embed = self.create_info_embed(
            f"🔒 Command Permissions - {ctx.guild.name}",
            f"Total: {len(permissions)} commands with custom permissions",
        )

        # Create list of commands
        commands = [f"`{perm.command_name}` → Rank {perm.required_rank}" for perm in permissions]

        # Split into chunks to avoid Discord field limits
        chunk_size = 20
        for i in range(0, len(commands), chunk_size):
            chunk = commands[i : i + chunk_size]
            embed.add_field(
                name=f"📋 Commands ({i + 1}-{min(i + chunk_size, len(commands))})"
                if len(commands) > chunk_size
                else "📋 Commands",
                value="\n".join(chunk),
                inline=False,
            )

        embed.set_footer(text="Use /config commands assign | unassign to manage permissions")
        await ctx.send(embed=embed)

    async def assign_permission(
        self,
        ctx: commands.Context[Tux],
        command_name: str,
        rank: int,
    ) -> None:
        """Set permission rank requirement for command."""
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

            # Check if command permission already exists
            existing = await self.bot.db.command_permissions.get_command_permission(ctx.guild.id, command_name)
            if existing:
                embed = self.create_warning_embed(
                    "⚠️ Command Already Restricted",
                    f"Command `{command_name}` already requires rank **{existing.required_rank}**.\n\nUse `/config commands unassign {command_name}` to remove the restriction first.",
                )
                await ctx.send(embed=embed)
                return

            # Create command permission
            await self.bot.db.command_permissions.set_command_permission(
                guild_id=ctx.guild.id,
                command_name=command_name,
                required_rank=rank,
            )

            embed = self.create_success_embed(
                "✅ Command Permission Set",
                f"Command `{command_name}` now requires rank **{rank}** (**{rank_obj.name}**).",
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await self.handle_error(ctx, e, "set command permission")

    async def remove_permission(self, ctx: commands.Context[Tux], command_name: str) -> None:
        """Remove permission requirement from command."""
        assert ctx.guild

        await ctx.defer()

        try:
            # Check if command permission exists
            existing = await self.bot.db.command_permissions.get_command_permission(ctx.guild.id, command_name)
            if not existing:
                embed = self.create_error_embed(
                    "❌ No Permission Found",
                    f"Command `{command_name}` has no custom permission requirements.",
                )
                await ctx.send(embed=embed)
                return

            # Remove command permission
            await self.bot.db.command_permissions.delete_where(
                filters=(PermissionCommand.guild_id == ctx.guild.id) & (PermissionCommand.command_name == command_name),
            )

            embed = self.create_success_embed(
                "✅ Command Permission Removed",
                f"Command `{command_name}` no longer has custom permission requirements.",
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await self.handle_error(ctx, e, "remove command permission")
