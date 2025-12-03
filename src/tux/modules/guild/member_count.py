"""
Guild member count display commands.

This module provides commands to display member statistics for Discord servers,
including total member count, human users, and bot counts.
"""

from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.ui.embeds import EmbedCreator


class MemberCount(BaseCog):
    """Discord cog for displaying guild member statistics."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the member count cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.hybrid_command(
        name="membercount",
        aliases=["mc", "members"],
        description="Shows server member count",
    )
    @commands.guild_only()
    async def member_count(self, ctx: commands.Context[Tux]) -> None:
        """
        Show the member count for the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The discord context object.
        """
        assert ctx.guild

        # Get the member count for the server (total members)
        members = ctx.guild.member_count
        # Get the number of humans in the server (subtract bots from total members)
        humans = sum(not member.bot for member in ctx.guild.members)
        # Get the number of bots in the server (subtract humans from total members)
        bots = sum(member.bot for member in ctx.guild.members if member.bot)

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Member Count",
        )

        embed.add_field(name="Members", value=str(members), inline=True)
        embed.add_field(name="Humans", value=str(humans), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Set up the MemberCount cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(MemberCount(bot))
