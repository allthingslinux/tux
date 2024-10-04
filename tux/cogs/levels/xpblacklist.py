import discord
from discord.ext import commands

from tux.bot import Tux
from tux.cogs.services.levels import LevelsService
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks
from tux.utils.flags import generate_usage


class XpBlacklist(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_service = LevelsService(bot)
        self.xp_blacklist.usage = generate_usage(self.xp_blacklist)

    @commands.guild_only()
    @checks.has_pl(2)
    @commands.hybrid_command(
        name="xpblacklist",
        aliases=["levelblacklist", "levelbl", "xpbl"],
    )
    async def xp_blacklist(self, ctx: commands.Context[Tux], member: discord.Member) -> None:
        """
        Blacklists or unblacklists a member from levelling.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to XP blacklist.
        """

        if ctx.guild is None:
            await ctx.send("This command can only be executed within a guild.")
            return

        state = await self.levels_service.levels_controller.toggle_blacklist(member.id, ctx.guild.id)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Blacklist - {member}",
            description=f"{member} has been {'blacklisted' if state else 'unblacklisted'} from gaining XP.",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(XpBlacklist(bot))
