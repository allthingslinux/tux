"""
Level and XP display commands.

This module provides commands to view user levels and XP points earned through
message activity. Users can check their own level or view other members' levels.
"""

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.modules.features.levels import LevelsService
from tux.shared.config import CONFIG
from tux.ui.embeds import EmbedCreator, EmbedType


class Level(BaseCog):
    """Discord cog for level and XP display commands.

    Provides functionality to display user levels and XP points earned through
    message activity. Supports viewing both personal and other members' levels
    with optional progress bars and XP caps.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Level cog.

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

    @commands.guild_only()
    @commands.hybrid_command(
        name="level",
        aliases=["lvl", "rank", "xp"],
    )
    async def level(
        self,
        ctx: commands.Context[Tux],
        member: discord.User | discord.Member | None = None,
    ) -> None:
        """
        Fetch the XP and level for a member (or the person who runs the command if no member is provided).

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.User
            The member to fetch XP and level for.
        """
        if ctx.guild is None:
            await ctx.send("This command can only be executed within a guild.")
            return

        if member is None:
            member = ctx.author

        logger.debug(f"Level check for {member.name} ({member.id}) in {ctx.guild.name}")

        xp: float = await self.db.levels.get_xp(member.id, ctx.guild.id)
        level: int = await self.db.levels.get_level(member.id, ctx.guild.id)

        logger.debug(f"Retrieved stats for {member.id}: Level {level}, XP {xp}")

        level_display: int
        xp_display: str
        if self.levels_service.enable_xp_cap and level >= self.levels_service.max_level:
            max_xp: float = self.levels_service.calculate_xp_for_level(
                self.levels_service.max_level,
            )
            level_display = self.levels_service.max_level
            xp_display = f"{round(max_xp)} (limit reached)"
            logger.debug(f"XP cap reached for {member.id}")
        else:
            level_display = level
            xp_display = f"{round(xp)}"

        if CONFIG.XP_CONFIG.SHOW_XP_PROGRESS:
            xp_progress: int
            xp_required: int
            xp_progress, xp_required = self.levels_service.get_level_progress(xp, level)
            progress_bar: str = self.levels_service.generate_progress_bar(
                xp_progress,
                xp_required,
            )

            embed: discord.Embed = EmbedCreator.create_embed(
                embed_type=EmbedType.DEFAULT,
                title=f"Level {level_display}",
                description=f"Progress to Next Level:\n{progress_bar}",
                custom_color=discord.Color.blurple(),
                custom_author_text=f"{member.name}",
                custom_author_icon_url=member.display_avatar.url,
                custom_footer_text=f"Total XP: {xp_display}",
            )
        else:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.DEFAULT,
                description=f"**Level {level_display}** - `XP: {xp_display}`",
                custom_color=discord.Color.blurple(),
                custom_author_text=f"{member.name}",
                custom_author_icon_url=member.display_avatar.url,
            )

        await ctx.send(embed=embed)
        logger.info(
            f"📊 Level info sent for {member.name} ({member.id}): Level {level_display}, XP {xp_display}",
        )


async def setup(bot: Tux) -> None:
    """Set up the Level cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Level(bot))
