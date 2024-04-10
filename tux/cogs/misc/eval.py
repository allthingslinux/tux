import discord
import utils.godbolt
from discord.ext import commands


class Eval(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="eval")
    async def eval(self, ctx: commands.Context[commands.Bot], lang, *, code, options=None) -> None:
        langs = {
            "haskell": "ghc961",
            "C": "cclang1810",
            "C++": "cclang1810",
            "python": "python312",
            "asm": "nasm21601",
        }
        if langs.get(lang) is None:
            await ctx.send("Not a valid compiler! Choose from haskell, C, C++ or python")
            return
        cls = code.replace("`", "")
        evalstr = utils.godbolt.getoutput(cls, langs.get(lang), options)
        genone = evalstr.partition("\n")[0]
        evalstr.partition("\n")[1]
        genthree = evalstr.partition("\n")[2]
        embed = discord.Embed(color=0xFFFFFF)
        embed.set_author(name=ctx.author)
        embed.set_thumbnail(url="https://www.vectorlogo.zone/logos/godbolt/godbolt-ar21.png")
        embed.add_field(name=genone[1:], value="", inline=True)
        embed.add_field(name="Result", value=f"```{lang}\n{genthree}\n```", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="genasm")
    async def genasm(
        self, ctx: commands.Context[commands.Bot], lang, *, code, options=None
    ) -> None:
        langs = {
            "haskell": "ghc961",
            "C": "cclang1810",
            "C++": "cclang1810",
            "python": "python312",
            "asm": "nasm21601",
        }
        if langs.get(lang) is None:
            await ctx.send("Not a valid compiler! Choose from haskell, C or C++")
            return
        cls = code.replace("`", "")
        evalstr = utils.godbolt.generateasm(cls, langs[lang], options)
        genone = evalstr.partition("\n")[0]
        _gentwo = evalstr.partition("\n")[
            1
        ]  # this variable sometimes contains something, sometimes does not.
        genthree = evalstr.partition("\n")[2]
        if len(genthree) >= 250 or len(_gentwo) >= 250:
            genla = _gentwo + genthree
            gencom = (
                genla[:250]
                + "\n The assembly was truncated, please go to GodBolt to see the full assembly."
            )
        else:
            gencom = _gentwo + genthree
        embed = discord.Embed(color=0xFFFFFF)
        embed.set_author(name=ctx.author)
        embed.set_thumbnail(url="https://www.vectorlogo.zone/logos/godbolt/godbolt-ar21.png")
        embed.add_field(name=genone[1:], value="", inline=True)
        embed.add_field(name="Result", value=f"```asm\n{gencom}\n```", inline=False)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Eval(bot))
