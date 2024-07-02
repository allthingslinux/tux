import re

from discord.ext import commands

from tux.services import godbolt
from tux.utils.embeds import EmbedCreator

ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
remove_ticks = re.compile(r"\`")

compiler_map = {
    "hs": "ghc961",
    "haskell": "ghc961",
    "c": "cclang1810",
    "cpp": "cclang1810",
    "c++": "cclang1810",
    "rs": "r1770",
    "rust": "r1770",
    "julia": "julia_nightly",
    "py": "python312",
    "python": "python312",
    "scala": "scalac300",
    "go": "gccgo131",
    "kotlin": "kotlinc1920",
    "kt": "kotlinc1920",
    "kot": "kotlinc1920",
    "erlang": "erl2622",
    "dart": "dart322",
    "swift": "swift59",
    "zig": "z090",
    "java": "java2200",
    "fsharp": "dotnet707fsharp",
    "fs": "dotnet707fsharp",
    "csharp": "dotnet707csharp",
    "cs": "dotnet707csharp",
    "ts": "tsc_0_0_35_gc",
    "typescript": "tsc_0_0_35_gc",
}


class Run(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def remove_ansi(self, ansi: str) -> str:
        """
        Converts ANSI encoded text into non-ANSI.

        Parameters
        ----------
        ansi : str
            The ANSI encoded text.

        Returns
        -------
        str
            The non-ANSI encoded text.
        """

        return ansi_escape.sub("", ansi)

    def remove_backticks(self, ticks: str) -> str:
        """
        Removes backticks from the provided string.

        Parameters
        ----------
        ticks : str
            The string containing backticks.

        Returns
        -------
        str
            The string without backticks.
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

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is invoked.
        compiler_map : dict[str, str]
            A dictionary containing mappings from a language to its compiler.
        code : str
            A string consisting of the code.
        options : str | None
            Optional arguments to be passed to the compiler.

        Returns
        -------
        tuple[str, str, str] | None
            A tuple containing the filtered output, the first few lines of the output, and the normalized language.
        """

        cleaned_code = self.remove_backticks(code)
        normalized_lang = cleaned_code.splitlines().pop(0)
        cleaned_code = "\n".join(cleaned_code.splitlines()[1:])

        if normalized_lang not in compiler_map:
            embed = EmbedCreator.create_error_embed(
                title="Fatal exception occurred!",
                description="Bad Formatting",
                ctx=ctx,
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

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is invoked.
        compiler_map : dict[str, str]
            A dictionary containing mappings from a language to its compiler.
        code : str
            A string consisting of the code.
        options : str | None
            Optional arguments to be passed to the compiler.

        Returns
        -------
        tuple[str, str, str] | None
            A tuple containing the filtered output, the first few lines of the output, and the normalized language.
        """

        cleaned_code = self.remove_backticks(code)
        normalized_lang = cleaned_code.splitlines().pop(0)
        cleaned_code = "\n".join(cleaned_code.splitlines()[1:])

        if normalized_lang not in compiler_map:
            embed = EmbedCreator.create_error_embed(
                title="Fatal exception occurred!",
                description="Bad Formatting",
                ctx=ctx,
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
    ) -> None:
        """
        A generalized version of an embed.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is invoked.
        gen_one : str
            The first few lines of the output.
        output : str
            The output.
        lang : str
            The language of the code.

        Returns
        -------
        None
        """

        embed = EmbedCreator.create_info_embed(
            title="Compilation provided by https://godbolt.org/",
            description=f"```{lang}\n{output}\n```",
            ctx=ctx,
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="run",
        aliases=["r"],
        help="Run code in various languages.",
        usage="$run `language`\n```code```",
    )
    async def run(self, ctx: commands.Context[commands.Bot], *, code: str):
        """
        A code evaluator. The code must be provided in  backticks along with the syntax highlighting to identify the language. Use short form syntax for the language. Available languages are Haskell, C, Rust, Julia, Python, C++.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is invoked.
        code : str
            The code to be evaluated.

        Returns
        -------
        None
        """

        msg = await ctx.send("<a:typing:1236671731859722270>")

        (filtered_output, gen_one, normalized_lang) = await self.generalized_code_executor(
            ctx,
            compiler_map,
            code,
        )
        await msg.delete()
        if filtered_output == "" and gen_one == "" and normalized_lang == "":
            return
        await self.send_embedded_reply(
            ctx,
            gen_one,
            self.remove_ansi(filtered_output),
            normalized_lang,
        )

    @run.error
    async def run_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        """
        A generalized error handler for the run command.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is invoked.
        error : Exception
            The error that occurred.
        """

        desc = ""
        if isinstance(error, commands.CommandInvokeError):
            desc = error.original
        if isinstance(error, commands.MissingRequiredArgument):
            desc = f"Missing required argument: `{error.param.name}`"

        embed = EmbedCreator.create_error_embed(
            title="Fatal exception occurred!",
            description=str(desc),
            ctx=ctx,
        )

        await ctx.send(embed=embed)

    @commands.command(name="languages", aliases=["langs"], help="List all the supported languages.")
    async def languages(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Lists all the supported languages.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is invoked.

        Returns
        -------
        None
        """

        embed = EmbedCreator.create_info_embed(
            title="Supported Languages",
            description=f"```{', '.join(compiler_map.keys())}```",
            ctx=ctx,
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Run(bot))
