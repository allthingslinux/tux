import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers.levels import LevelsController
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks
from tux.utils.flags import generate_usage
from tux.utils.functions import valid_xplevel_input


class LevelSet(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_controller = LevelsController()
        self.level_set.usage = generate_usage(self.level_set)

    @commands.guild_only()
    @checks.has_pl(2)
    @commands.hybrid_command(name="levelset", aliases=["lvlset"])
    async def level_set(self, ctx: commands.Context[Tux], member: discord.Member, new_level: int) -> None:
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

        old_level = await self.levels_controller.get_level(member.id, ctx.guild.id)
        old_xp = await self.levels_controller.get_xp(member.id, ctx.guild.id)

        embed_result: discord.Embed | None = valid_xplevel_input(new_level) or discord.Embed()
        if embed_result:
            await ctx.send(embed=embed_result)
            return

        await self.levels_controller.set_level(member.id, ctx.guild.id, new_level, member, ctx.guild)

        new_xp = await self.levels_controller.get_xp(member.id, ctx.guild.id)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"Level Set - {member}",
            description=f"{member}'s level has been updated from **{old_level}** to **{new_level}**\nTheir XP has been updated from **{old_xp}** to **{new_xp}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(LevelSet(bot))
