import datetime

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.cogs.services.levels import LevelsService
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks
from tux.utils.flags import generate_usage


class XPSet(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_service = LevelsService(bot)
        self.xp_set.usage = generate_usage(self.xp_set)

    @commands.guild_only()
    @checks.has_pl(2)
    @commands.hybrid_command(name="xpset")
    async def xp_set(self, ctx: commands.Context[Tux], member: discord.Member, xp_amount: int) -> None:
        """
        Sets the xp of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to set the XP for.
        """
        if ctx.guild is None:
            await ctx.send("This command can only be executed within a guild.")
            return

        # The condition here was incorrect
        if embed_result := self.levels_service.valid_xplevel_input(xp_amount):
            await ctx.send(embed=embed_result)
            return

        old_level = await self.levels_service.levels_controller.get_level(member.id, ctx.guild.id)
        old_xp = await self.levels_service.levels_controller.get_xp(member.id, ctx.guild.id)

        new_level = self.levels_service.calculate_level(xp_amount)
        await self.levels_service.levels_controller.update_xp_and_level(
            member.id,
            ctx.guild.id,
            xp_amount,
            new_level,
            datetime.datetime.now(datetime.UTC),
        )

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Set - {member}",
            description=f"{member}'s XP has been updated from **{old_xp}** to **{xp_amount}**\nTheir level has been updated from **{old_level}** to **{new_level}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(XPSet(bot))
