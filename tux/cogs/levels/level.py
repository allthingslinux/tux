import discord
from discord.ext import commands
import EmbedBuilder

from tux.bot import Tux
from tux.database.controllers.levels import LevelsController
from tux.utils.flags import generate_usage


class Level(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_controller = LevelsController()
        self.level.usage = generate_usage(self.level)

    @commands.guild_only()
    @commands.hybrid_command(
        name="level",
        aliases=["lvl", "rank", "xp"],
    )
    async def level(self, ctx: commands.Context[Tux], user: discord.User | discord.Member | None = None) -> None:
        """
        Fetches the XP and level for a user and sends it back using a file.

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

        if user is None:
            user = ctx.author

        guild_id = ctx.guild.id
        user_id = user.id



        xp = await self.levels_controller.get_xp(user_id, guild_id)
        level = await self.levels_controller.get_level(user_id, guild_id)

        const embed = new EmbedBuilder()
            .setAuthor({
                name: "Tux",
            })
        .setTitle("Experience")
        .setDescription("Your Level: {level}\nYour Exp: {xp}");

        await message.reply({ embeds: [embed] });



async def setup(bot: Tux) -> None:
    await bot.add_cog(Level(bot))
