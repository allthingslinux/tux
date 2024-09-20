import discord
from discord.ext import commands

from tux.bot import Tux
from tux.ui.embeds import EmbedCreator

client = discord.Client


usermessages = []


class Levels(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="level",
        aliases=["lvl"],
    )
    @commands.guild_only()
    async def main(self, ctx: commands.Context[Tux]) -> None:
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name="Tux - EXP",
            title="You are level level",
            description="Your have exp exp!",
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Levels(bot))
