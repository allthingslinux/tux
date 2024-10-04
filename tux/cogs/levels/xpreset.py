import discord
from discord.ext import commands

from tux.bot import Tux
from tux.cogs.services.levels import LevelsService
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks
from tux.utils.flags import generate_usage


class XpReset(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_service = LevelsService(bot)
        self.xp_reset.usage = generate_usage(self.xp_reset)

    @commands.guild_only()
    @checks.has_pl(2)
    @commands.hybrid_command(name="xpreset", aliases=["levelreset", "lvlreset"])
    async def xp_reset(self, ctx: commands.Context[Tux], member: discord.Member) -> None:
        """
        Resets the xp and level of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to reset the XP for.
        """
        if ctx.guild is None:
            await ctx.send("This command can only be executed within a guild.")
            return

        old_xp = await self.levels_service.levels_controller.get_xp(member.id, ctx.guild.id)
        await self.levels_service.levels_controller.reset_xp(member.id, ctx.guild.id)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Reset - {member}",
            description=f"{member}'s XP has been reset from **{old_xp}** to **0**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(XpReset(bot))
