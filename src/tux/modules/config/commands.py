"""Command permission management for the config system."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

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
                'No commands have custom permission requirements.\n\nUse `/config overview` → Click **"🤖 Command Permissions"** to set requirements.',
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

        embed.set_footer(text="Use /config overview → Command Permissions to manage permissions")
        await ctx.send(embed=embed)
