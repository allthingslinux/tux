import datetime

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.cogs.services.levels import LevelsService
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks
from tux.utils.flags import generate_usage


class LevelSet(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_service = LevelsService(bot)
        self.level_set.usage = generate_usage(self.level_set)

    @commands.guild_only()
    @checks.has_pl(2)
    @commands.hybrid_command(name="levelset", aliases=["lvlset"])
    async def level_set(self, ctx: commands.Context[Tux], member: discord.Member, new_level: int) -> None:
        """
        Sets the level of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to set the level for.
        """

        if ctx.guild is None:
            await ctx.send("This command can only be executed within a guild.")
            return

        old_level = await self.levels_service.levels_controller.get_level(member.id, ctx.guild.id)
        old_xp = await self.levels_service.levels_controller.get_xp(member.id, ctx.guild.id)

        if embed_result := self.levels_service.valid_xplevel_input(new_level) or discord.Embed():
            await ctx.send(embed=embed_result)
            return

        new_xp = self.levels_service.calculate_xp_for_level(new_level)
        await self.levels_service.levels_controller.update_xp_and_level(
            member.id,
            ctx.guild.id,
            new_xp,
            new_level,
            datetime.datetime.now(datetime.UTC),
        )

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"Level Set - {member}",
            description=f"{member}'s level has been updated from **{old_level}** to **{new_level}**\nTheir XP has been updated from **{old_xp}** to **{new_xp}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(LevelSet(bot))
