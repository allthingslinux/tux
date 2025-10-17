"""Configuration overview commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from tux.ui.embeds import EmbedCreator, EmbedType

if TYPE_CHECKING:
    from tux.core.bot import Tux


class ConfigOverview:
    """Overview and status commands for config system."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the config overview handler.

        Parameters
        ----------
        bot : Tux
            The Discord bot instance.
        """
        self.bot = bot

    async def overview_command(self, ctx: commands.Context[Tux]) -> None:  # noqa: PLR0912, PLR0915
        # sourcery skip: low-code-quality
        """View complete guild configuration overview."""
        assert ctx.guild

        await ctx.defer()

        # Fetch all configuration data
        guild_config = await self.bot.db.guild_config.get_config_by_guild_id(ctx.guild.id)
        permission_ranks = await self.bot.db.guild_permissions.get_permission_ranks_by_guild(ctx.guild.id)
        assignments = await self.bot.db.permission_assignments.get_assignments_by_guild(ctx.guild.id)
        command_perms = await self.bot.db.command_permissions.get_all_command_permissions(ctx.guild.id)

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
        log_channels: list[str] = []
        if guild_config:
            if guild_config.mod_log_id:
                log_channels.append(f"**Mod:** <#{guild_config.mod_log_id}>")
            if guild_config.audit_log_id:
                log_channels.append(f"**Audit:** <#{guild_config.audit_log_id}>")
            if guild_config.join_log_id:
                log_channels.append(f"**Join:** <#{guild_config.join_log_id}>")
            if guild_config.private_log_id:
                log_channels.append(f"**Private:** <#{guild_config.private_log_id}>")
            if guild_config.report_log_id:
                log_channels.append(f"**Report:** <#{guild_config.report_log_id}>")
            if guild_config.dev_log_id:
                log_channels.append(f"**Dev:** <#{guild_config.dev_log_id}>")
            if guild_config.jail_channel_id:
                log_channels.append(f"**Jail:** <#{guild_config.jail_channel_id}>")

            if log_channels:
                embed.add_field(
                    name="📝 Log Channels",
                    value="\n".join(log_channels),
                    inline=False,
                )

        # Permission overview
        if permission_ranks:
            enabled_ranks = permission_ranks
            embed.add_field(
                name="🎯 Permission System",
                value=f"**Ranks:** {len(enabled_ranks)}\n**Assignments:** {len(assignments)} roles\n**Restrictions:** {len(command_perms)} commands",
                inline=True,
            )

        # Onboarding status
        if guild_config:
            status_icon = "✅" if guild_config.onboarding_completed else "⏳"
            stage = guild_config.onboarding_stage or "unknown"
            embed.add_field(
                name="🚀 Setup Status",
                value=f"{status_icon} {stage.replace('_', ' ').title()}",
                inline=True,
            )

        # Command restrictions
        if command_perms:
            embed.add_field(
                name="🔒 Restricted Commands",
                value=str(len(command_perms)),
                inline=True,
            )

        # Recommendations
        recommendations: list[str] = []

        if not permission_ranks:
            recommendations.append("• Run `/config wizard` to set up your server")
        elif not assignments:
            recommendations.append("• Assign roles to permission ranks with `/config role assign`")
        elif not log_channels:
            recommendations.append("• Set up log channels in the setup wizard")

        if not guild_config or not guild_config.onboarding_completed:
            recommendations.append("• Complete initial setup with `/config wizard`")

        if recommendations:
            embed.add_field(
                name="💡 Recommendations",
                value="\n".join(recommendations),
                inline=False,
            )

        embed.set_footer(text="Use /config rank | role | command | wizard for detailed management")
        await ctx.send(embed=embed)
