from discord.ext import commands

from tux.utils import godbolt
from tux.utils.embeds import EmbedCreator


class Eval(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_embedded_reply(
        self,
        ctx: commands.Context[commands.Bot],
        gen_one: str,
        output: str,
        lang: str,
    ):
        embed = EmbedCreator.create_info_embed(
            title="Eval",
            description="Here is the output of the code.",
            ctx=ctx,
        )

        embed.set_thumbnail(url="https://www.vectorlogo.zone/logos/godbolt/godbolt-ar21.png")
        embed.add_field(name=gen_one[1:], value="", inline=True)
        embed.add_field(name="Result", value=f"```{lang}\n{output}\n```", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="eval")
    async def eval(
        self,
        ctx: commands.Context[commands.Bot],
        lang: str,
        *,
        code: str,
        options: str | None = None,
    ):
        compiler_map = {
            "haskell": "ghc961",
            "c": "cclang1810",
            "cpp": "cclang1810",
            "python": "python312",
        }

        normalized_lang = lang.lower()
        if normalized_lang not in compiler_map:
            await ctx.send("Not a valid compiler! Choose from Haskell, C, C++, or Python.")
            return

        cleaned_code = code.strip("`")
        compiler_id = compiler_map[normalized_lang]
        output = godbolt.getoutput(cleaned_code, compiler_id, options)

        if output is None:
            await ctx.send("Failed to get output from compiler.")
            return

        lines = output.split("\n")
        gen_one = lines[0]
        filtered_output = "\n".join(lines[1:])

        await self.send_embedded_reply(ctx, gen_one, filtered_output, lang)

    @commands.command(name="genasm")
    async def genasm(
        self,
        ctx: commands.Context[commands.Bot],
        lang: str,
        *,
        code: str,
        options: str | None = None,
    ):
        compiler_map = {"haskell": "ghc961", "c": "cclang1810", "cpp": "cclang1810"}

        normalized_lang = lang.lower()
        if normalized_lang not in compiler_map:
            await ctx.send("Not a valid compiler! Choose from Haskell, C, or C++.")
            return

        cleaned_code = code.strip("`")
        compiler_id = compiler_map[normalized_lang]
        output = godbolt.generateasm(cleaned_code, compiler_id, options)

        if output is None:
            await ctx.send("Failed to get assembly output.")
            return

        lines = output.split("\n")
        gen_one = lines[0]
        filtered_output = "\n".join(lines[1:])

        await self.send_embedded_reply(ctx, gen_one, filtered_output, "asm")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Eval(bot))
