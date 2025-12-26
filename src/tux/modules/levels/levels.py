"""
Level and XP management commands for administrators.

This module provides administrative commands to manage user levels and XP points,
including setting levels/XP, resetting progress, and blacklisting users from
leveling. These commands require appropriate permissions and are intended for
server moderation and management purposes.
"""

import datetime

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.modules.features.levels import LevelsService
from tux.shared.config import CONFIG
from tux.ui.embeds import EmbedCreator, EmbedType


class Levels(BaseCog):
    """Discord cog for administrative level and XP management commands.

    Provides commands for server administrators to manage user levels and XP,
    including setting levels/XP values, resetting progress, and toggling XP
    blacklists. All commands require appropriate permissions and automatically
    update user roles based on level changes.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Levels cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

        # Check if XP roles are configured
        if self.unload_if_missing_config(
            condition=not CONFIG.XP_CONFIG.XP_ROLES,
            config_name="XP_ROLES configuration",
        ):
            return

        self.levels_service = LevelsService(bot)

    @commands.hybrid_group(
        name="levels",
        aliases=["lvls"],
    )
    @commands.guild_only()
    async def levels(
        self,
        ctx: commands.Context[Tux],
    ) -> None:
        """Level and XP management related commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help("levels")

    @requires_command_permission()
    @commands.guild_only()
    @levels.command(name="set", aliases=["s"])
    async def set(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        new_level: int,
    ) -> None:
        """
        Set the level of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to set the level for.
        """
        assert ctx.guild

        old_level: int = await self.db.levels.get_level(member.id, ctx.guild.id)
        old_xp: float = await self.db.levels.get_xp(member.id, ctx.guild.id)

        if embed_result := self.levels_service.valid_xplevel_input(new_level):
            logger.warning(
                f"Validation failed: Level {new_level} rejected for {member.name} ({member.id}) - out of valid range",
            )
            await ctx.send(embed=embed_result)
            return

        new_xp: float = self.levels_service.calculate_xp_for_level(new_level)
        await self.db.levels.update_xp_and_level(
            member.id,
            ctx.guild.id,
            new_xp,
            new_level,
            datetime.datetime.now(datetime.UTC),
        )

        # Update roles based on the new level
        await self.levels_service.update_roles(member, ctx.guild, new_level)

        logger.info(
            f"⚙️ Level manually set for {member.name} ({member.id}) by {ctx.author.name}: {old_level} -> {new_level}",
        )

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"Level Set - {member}",
            description=f"{member}'s level has been updated from **{old_level}** to **{new_level}**\nTheir XP has been updated from **{round(old_xp)}** to **{round(new_xp)}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)

    @requires_command_permission()
    @commands.guild_only()
    @levels.command(name="setxp", aliases=["sxp"])
    async def set_xp(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        xp_amount: int,
    ) -> None:
        """
        Set the xp of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to set the XP for.
        """
        assert ctx.guild

        if embed_result := self.levels_service.valid_xplevel_input(xp_amount):
            logger.warning(
                f"Validation failed: XP amount {xp_amount} rejected for {member.name} ({member.id}) - out of valid range",
            )
            await ctx.send(embed=embed_result)
            return

        old_level: int = await self.db.levels.get_level(member.id, ctx.guild.id)
        old_xp: float = await self.db.levels.get_xp(member.id, ctx.guild.id)

        new_level: int = self.levels_service.calculate_level(xp_amount)
        await self.db.levels.update_xp_and_level(
            member.id,
            ctx.guild.id,
            float(xp_amount),
            new_level,
            datetime.datetime.now(datetime.UTC),
        )

        # Update roles based on the new level
        await self.levels_service.update_roles(member, ctx.guild, new_level)

        logger.info(
            f"⚙️ XP manually set for {member.name} ({member.id}) by {ctx.author.name}: {round(old_xp)} -> {xp_amount} (Level: {old_level} -> {new_level})",
        )

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Set - {member}",
            description=f"{member}'s XP has been updated from **{round(old_xp)}** to **{(xp_amount)}**\nTheir level has been updated from **{old_level}** to **{new_level}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)

    @requires_command_permission()
    @commands.guild_only()
    @levels.command(name="reset", aliases=["r"])
    async def reset(self, ctx: commands.Context[Tux], member: discord.Member) -> None:
        """
        Reset the xp and level of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to reset the XP for.
        """
        assert ctx.guild

        old_xp: float = await self.db.levels.get_xp(member.id, ctx.guild.id)
        await self.db.levels.reset_xp(member.id, ctx.guild.id)

        logger.info(
            f"XP reset for {member.name} ({member.id}) by {ctx.author.name}: {round(old_xp)} -> 0",
        )

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Reset - {member}",
            description=f"{member}'s XP has been reset from **{round(old_xp)}** to **0**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)

    @requires_command_permission()
    @commands.guild_only()
    @levels.command(name="blacklist", aliases=["bl"])
    async def blacklist(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
    ) -> None:
        """
        Blacklists or unblacklists a member from leveling.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to XP blacklist.
        """
        assert ctx.guild

        state: bool = await self.db.levels.toggle_blacklist(member.id, ctx.guild.id)

        logger.info(
            f"🚫 XP blacklist toggled for {member.name} ({member.id}) by {ctx.author.name}: {'BLACKLISTED' if state else 'UNBLACKLISTED'}",
        )

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Blacklist - {member}",
            description=f"{member} has been {'blacklisted' if state else 'unblacklisted'} from gaining XP.",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Set up the Levels cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Levels(bot))
