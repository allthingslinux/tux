import discord
from discord.ext import commands

from tux.bot import Tux
from tux.database.controllers.levels import LevelsController
from tux.utils import checks
from tux.utils.flags import generate_usage


class XpBlacklist(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_controller = LevelsController()
        self.xp_blacklist.usage = generate_usage(self.xp_blacklist)

    @commands.guild_only()
    @checks.has_pl(2)
    @commands.hybrid_command(
        name="xpblacklist",
        aliases=["rankblacklist", "levelblacklist", "rankbl", "levelbl", "xpbl"],
    )
    async def xp_blacklist(self, ctx: commands.Context[Tux], user: discord.User) -> None:
        """
        Blacklists or unblacklists a user from levelling.

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

        guild_id = ctx.guild.id
        user_id = user.id

        state = await self.levels_controller.toggle_blacklist(user_id, guild_id)
        const embed = new EmbedBuilder()
             .setAuthor({
                name: "Tux",
            })
            .setTitle("EXP Blacklist Confirm")
            .setDescription("{user_id} has been (un)blacklisted from gaining exp!");

await message.reply({ embeds: [embed] });



async def setup(bot: Tux) -> None:
    await bot.add_cog(XpBlacklist(bot))
