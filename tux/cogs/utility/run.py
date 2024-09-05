import re

from discord.ext import commands

from tux.bot import Tux
from tux.ui.embeds import EmbedCreator
from tux.wrappers import godbolt

ansi_re = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
ticks_re = re.compile(r"\`")

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
    def __init__(self, bot: Tux):
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

        return ansi_re.sub("", ansi)

    def remove_backticks(self, st: str) -> str:
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

        return ticks_re.sub("", st)

    async def generalized_code_executor(
        self,
        ctx: commands.Context[Tux],
        compiler_map: dict[str, str],
        code: str,
        options: str | None = None,
    ) -> tuple[str, str, str]:
        """
        A generalized version of the code executor.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        compiler_map : dict[str, str]
            A dictionary containing mappings from a language to its compiler.
        code : str
            A string consisting of the code.
        options : str | None
            Optional arguments to be passed to the compiler.

        Returns
        -------
        tuple[str, str, str]
            A tuple containing the filtered output, the first few lines of the output, and the normalized language.
        """

        cleaned_code = self.remove_backticks(code)
        normalized_lang = cleaned_code.splitlines().pop(0)
        cleaned_code = "\n".join(cleaned_code.splitlines()[1:])

        if normalized_lang not in compiler_map:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Fatal exception occurred!",
                description="Bad Formatting",
            )
            await ctx.send(embed=embed)
            return ("", "", "")

        compiler_id = compiler_map[normalized_lang]
        output = godbolt.getoutput(cleaned_code, compiler_id, options)

        if output is None:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Fatal exception occurred!",
                description="failed to get output from the compiler",
            )
            await ctx.send(embed=embed, ephemeral=True, delete_after=30)
            return ("", "", "")

        lines = output.split("\n")
        gen_one = lines[0]
        filtered_output = "\n".join(lines[1:])

        return (filtered_output, gen_one, normalized_lang)

    async def generalized_code_constructor(
        self,
        ctx: commands.Context[Tux],
        compiler_map: dict[str, str],
        code: str,
        options: str | None = None,
    ) -> tuple[str, str, str]:
        """
        A generalized version of the assembly generation function used previously.

        Parameters
        ----------
        ctx : commands.Context[Tux]
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
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Fatal exception occurred!",
                description="Bad Formatting",
            )
            await ctx.send(embed=embed, ephemeral=True, delete_after=30)
            return ("", "", "")

        compiler_id = compiler_map[normalized_lang]
        output = godbolt.generateasm(cleaned_code, compiler_id, options)

        if output is None:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Fatal exception occurred!",
                description="failed to get output from the compiler",
            )
            await ctx.send(embed=embed, ephemeral=True, delete_after=30)
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
        ctx: commands.Context[Tux],
        gen_one: str,
        output: str,
        lang: str,
    ) -> None:
        """
        A generalized version of an embed.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        gen_one : str
            The first few lines of the output.
        output : str
            The output.
        lang : str
            The language of the code.
        """

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Compilation provided by https://godbolt.org/",
            description=f"```{lang}\n{output}\n```",
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="run",
        aliases=["compile", "exec"],
        usage="run [code]",
    )
    async def run(
        self,
        ctx: commands.Context[Tux],
        *,
        code: str,
    ):
        """
        Run code in various languages. Code should be enclosed in triple backticks with syntax highlighting.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        code : str
            The code to be evaluated.
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
    async def run_error(
        self,
        ctx: commands.Context[Tux],
        error: Exception,
    ):
        """
        A generalized error handler for the run command.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        error : Exception
            The error that occurred.
        """

        desc = ""
        if isinstance(error, commands.CommandInvokeError):
            desc = error.original
        if isinstance(error, commands.MissingRequiredArgument):
            desc = f"Missing required argument: `{error.param.name}`"

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.ERROR,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Fatal exception occurred!",
            description=str(desc),
        )

        await ctx.send(embed=embed, ephemeral=True, delete_after=30)

    @commands.command(
        name="languages",
        aliases=["langs"],
        usage="languages",
    )
    async def languages(self, ctx: commands.Context[Tux]) -> None:
        """
        Lists all the supported languages.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        """

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Supported Languages",
            description=f"```{', '.join(compiler_map.keys())}```",
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Run(bot))
