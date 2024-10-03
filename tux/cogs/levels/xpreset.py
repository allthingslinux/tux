import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers.levels import LevelsController
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks
from tux.utils.flags import generate_usage


class XpReset(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_controller = LevelsController()
        self.xp_reset.usage = generate_usage(self.xp_reset)

    @commands.guild_only()
    @checks.has_pl(2)
    @commands.hybrid_command(name="xpreset", aliases=["rankreset", "levelreset", "lvlreset"])
    async def xp_reset(self, ctx: commands.Context[Tux], user: discord.User) -> None:
        """
        Resets the xp and level of a user.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The user to reset the XP for.
        """
        if ctx.guild is None:
            await ctx.send("This command can only be executed within a guild.")
            return

        guild_id = ctx.guild.id
        user_id = user.id

        xp = await self.levels_controller.get_xp(user_id, guild_id)

        member = ctx.guild.get_member(user_id)
        if member is None:
            await ctx.send("User not found in the guild.")
            return

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Set - {user}",
            description=f"{user}'s XP has been reset from **{xp}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(XpReset(bot))
