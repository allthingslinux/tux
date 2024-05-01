import re

from discord.ext import commands

from tux.services import godbolt
from tux.utils.embeds import EmbedCreator

ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
remove_ticks = re.compile(r"\`")


class Run(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def remove_ansi(self, ansi: str) -> str:
        """
        Converts ANSI encoded text into non-ANSI.

        Args:
         ansi: String to be passed

        Returns:
         str

        Raises:
         None
        """
        return ansi_escape.sub("", ansi)

    def remove_backticks(self, ticks: str) -> str:
        """
        Removes backticks from the provided string.

        Args:
         ticks: String to be passed.

        Returns:
         str

        Raises:
         None
        """

        return remove_ticks.sub("", ticks)

    async def generalized_code_executor(
        self,
        ctx: commands.Context[commands.Bot],
        compiler_map: dict[str, str],
        code: str,
        options: str | None = None,
    ) -> tuple[str, str, str]:
        """
        A generalized version of the code executor.

        Args:
         ctx: Used to send messages upon error.
         compiler_map: A dictionary containing mappings from a language to its compiler
         code: A string consisting of the code
         options: optional arguments to be passed to the compiler

        Returns:
          tuple[str,str,str] | None

        Raises:
          None
        """

        cleaned_code = self.remove_backticks(code)
        normalized_lang = cleaned_code.splitlines().pop(0)
        cleaned_code = "\n".join(cleaned_code.splitlines()[1:])
        if normalized_lang not in compiler_map:
            embed = EmbedCreator.create_error_embed(
                title="Fatal exception occurred!", description="bad formatting", ctx=ctx
            )
            await ctx.send(embed=embed)
            return ("", "", "")

        compiler_id = compiler_map[normalized_lang]
        output = godbolt.getoutput(cleaned_code, compiler_id, options)

        if output is None:
            embed = EmbedCreator.create_error_embed(
                title="Fatal exception occurred!",
                description="failed to get output from the compiler",
                ctx=ctx,
            )
            await ctx.send(embed=embed)
            return ("", "", "")

        lines = output.split("\n")
        gen_one = lines[0]
        filtered_output = "\n".join(lines[1:])

        return (filtered_output, gen_one, normalized_lang)

    async def generalized_code_constructor(
        self,
        ctx: commands.Context[commands.Bot],
        compiler_map: dict[str, str],
        code: str,
        options: str | None = None,
    ) -> tuple[str, str, str]:
        """
        A generalized version of the assembly generation function used previously.

        Args:
         ctx: Used to send messages upon error.
         compiler_map: A dictionary containing mappings from a language to its compiler
         code: A string consisting of the code
         options: optional arguments to be passed to the compiler

        Returns:
          tuple[str,str,str] | None

        Raises:
          None
        """

        cleaned_code = self.remove_backticks(code)
        normalized_lang = cleaned_code.splitlines().pop(0)
        cleaned_code = "\n".join(cleaned_code.splitlines()[1:])
        if normalized_lang not in compiler_map:
            embed = EmbedCreator.create_error_embed(
                title="Fatal exception occurred!", description="bad formatting", ctx=ctx
            )
            await ctx.send(embed=embed)
            return ("", "", "")

        compiler_id = compiler_map[normalized_lang]
        output = godbolt.generateasm(cleaned_code, compiler_id, options)

        if output is None:
            embed = EmbedCreator.create_error_embed(
                title="Fatal exception occurred!",
                description="failed to get output from the compiler",
                ctx=ctx,
            )
            await ctx.send(embed=embed)
            return ("", "", "")

        lines = output.split("\n")
        gen_one = lines[0]
        filtered_output = "\n".join(lines[1:])
        if len(filtered_output) > 3500:
            return (
                "The assembly is too big to fit! Please do it on the GodBolt website instead.",
                gen_one,
                normalized_lang,
            )

        return (filtered_output, gen_one, normalized_lang)

    async def send_embedded_reply(
        self,
        ctx: commands.Context[commands.Bot],
        gen_one: str,
        output: str,
        lang: str,
    ):
        """
        A generalized version of an embed.

        Args:
         ctx: Used to send the embed.
         gen_one: string containing the first few lines of the output
         output: output returned
         lang: the language used

        Returns:
          None

        Raises:
          None
        """

        embed = EmbedCreator.create_info_embed(
            title="Run",
            description="",
            ctx=ctx,
        )
        embed.set_thumbnail(url="https://www.vectorlogo.zone/logos/godbolt/godbolt-ar21.png")
        embed.add_field(name=gen_one[1:], value="", inline=True)
        embed.add_field(name="Result", value=f"```{lang}\n{output}\n```", inline=False)

        await ctx.send(embed=embed)

    async def cog_command_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ):
        desc = ""
        if isinstance(error, commands.CommandInvokeError):
            desc = error.original
        if isinstance(error, commands.MissingRequiredArgument):
            desc = f"Missing required argument: `{error.param.name}`"

        embed = EmbedCreator.create_error_embed(
            title="Fatal exception occurred!", description=desc, ctx=ctx
        )
        await ctx.send(embed=embed)

    @commands.command(name="run")
    async def run(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        code: str,
    ):
        """
        A code evaluator. The code must be provided in  backticks along with the syntax highlighting to identify the language. Use short form
        syntax for the language. Available languages are Haskell, C, Rust, Julia, Python, C++.

        Parameters
        ----------
         ctx: commands.Context
           The context in which the command is invoked.
         code : str
           A string consisting of the code

        Returns
        ---------
          None

        Raises
        --------
          None
        """

        msg = await ctx.send("<a:typing:1231270453021249598>")

        compiler_map = {
            "hs": "ghc961",
            "c": "cclang1810",
            "cpp": "cclang1810",
            "rs": "r1770",
            "julia": "julia_nightly",
            "py": "python312",
        }

        (filtered_output, gen_one, normalized_lang) = await self.generalized_code_executor(
            ctx, compiler_map, code
        )
        await msg.delete()
        if filtered_output == "" and gen_one == "" and normalized_lang == "":
            return
        await self.send_embedded_reply(
            ctx, gen_one, self.remove_ansi(filtered_output), normalized_lang
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Run(bot))
