import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers.levels import LevelsController
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks
from tux.utils.flags import generate_usage


class LevelSet(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_controller = LevelsController()
        self.level_set.usage = generate_usage(self.level_set)

    @commands.guild_only()
    @checks.has_pl(2)
    @commands.hybrid_command(name="levelset", aliases=["rankset", "lvlset"])
    async def level_set(self, ctx: commands.Context[Tux], user: discord.User, new_level: int) -> None:
        """
        Sets the xp of a user.

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

        guild_id = ctx.guild.id
        user_id = user.id
        old_level = await self.levels_controller.get_level(user_id, guild_id)
        old_xp = await self.levels_controller.get_xp(user_id, guild_id)

        member = ctx.guild.get_member(user_id)
        guild = ctx.guild

        if member is None:
            await ctx.send("User is not a member of the guild.")
            return

        await self.levels_controller.set_level(user_id, guild_id, new_level, member, guild)
        new_xp = await self.levels_controller.get_xp(user_id, guild_id)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"Level Set - {user}",
            description=f"{user}'s level has been updated from **{old_level}** to **{new_level}**\nTheir XP has been updated from **{old_xp}** to **{new_xp}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(LevelSet(bot))
