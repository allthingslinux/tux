import discord
from discord.ext import commands

from tux.bot import Tux
from tux.cogs.services.levels import LevelsService
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils.flags import generate_usage


class Level(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_service = LevelsService(bot)
        self.level.usage = generate_usage(self.level)

    @commands.guild_only()
    @commands.hybrid_command(
        name="level",
        aliases=["lvl", "rank", "xp"],
    )
    async def level(self, ctx: commands.Context[Tux], member: discord.Member | None = None) -> None:
        """
        Fetches the XP and level for a member and sends it back using a file.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to fetch XP and level for. If not specified, fetches for the command author.
        """

        if ctx.guild is None:
            await ctx.send("This command can only be executed within a guild.")
            return

        if member is None:
            member = ctx.author if isinstance(ctx.author, discord.Member) else None
            assert member

        xp = await self.levels_service.levels_controller.get_xp(member.id, ctx.guild.id)
        level = await self.levels_service.levels_controller.get_level(member.id, ctx.guild.id)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"Level - {member}",
            description=f"Level: **{level}** \nXP: **{round(xp)}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Level(bot))
