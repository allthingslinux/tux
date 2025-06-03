import re
from abc import ABC, abstractmethod

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.ui.embeds import EmbedCreator
from tux.utils.functions import generate_usage
from tux.wrappers import godbolt, wandbox

ansi_re = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
ticks_re = re.compile(r"```")


compiler_map_godbolt = {
    "hs": "ghc984",
    "haskell": "ghc984",
    "c": "g151",
    "cpp": "g151",
    "c++": "g151",
    "rs": "r1870",
    "rust": "r1870",
    "julia": "julia_nightly",
    "py": "python313",
    "python": "python313",
    "go": "gccgo151",
    "kotlin": "kotlinc2121",
    "kt": "kotlinc2121",
    "kot": "kotlinc2121",
    "swift": "swift61",
    "zig": "z0141",
    "java": "java2400",
    "fsharp": "dotnet80fsharpmono",
    "fs": "dotnet80fsharpmono",
    "csharp": "dotnet80csharpmono",
    "cs": "dotnet80csharpmono",
}

compiler_map_wandbox = {
    "bash": "bash",
    "sh": "bash",
    "d": "dmd-2.109.1",
    "elixir": "elixir-1.17.3",
    "erlang": "erlang-27.1",
    "groovy": "groovy-4.0.23",
    "javascript": "nodejs-20.17.0",
    "js": "nodejs-20.17.0",
    "lisp": "clisp-2.49",
    "lua": "lua-5.4.7",
    "nim": "nim-2.2.4",
    "ocaml": "ocaml-5.2.0",
    "pascal": "fpc-3.2.2",
    "perl": "perl-5.40.0",
    "php": "php-8.3.12",
    "pony": "pony-0.58.5",
    "r": "r-4.4.1",
    "ruby": "ruby-3.4.1",
    "sql": "sqlite-3.46.1",
    "swift": "swift-6.0.1",
    "typescript": "typescript-5.6.2",
    "ts": "typescript-5.6.2",
}


class CodeDispatch(ABC):
    def __init__(self, compiler_map: dict[str, str]):
        self.compiler_map = compiler_map

    async def run(self, lang: str, code: str, opts: str | None):
        language = self.compiler_map.get(lang)
        return None if language is None else await self._execute(language, code, opts)

    @abstractmethod
    async def _execute(self, lang: str, code: str, opts: str | None) -> str | None: ...


class GodboltService(CodeDispatch):
    async def _execute(self, lang: str, code: str, opts: str | None):
        if lang in {"c++", "cpp"}:
            opts = f"{' ' if opts is None else opts} -xc++ -lstdc++ -shared-libgcc"

        out = godbolt.getoutput(code, lang, opts)
        if not out:
            return None

        lines = out.split("\n")
        return "\n".join(lines[5:])


class WandboxService(CodeDispatch):
    async def _execute(self, lang: str, code: str, opts: str | None):
        output = ""
        temp = wandbox.getoutput(code, lang, opts)
        if not temp:
            return None
        if (
            temp["compiler_error"] != "" and self.compiler_map.get("nim") != lang
        ):  # Nim decides to do some absolutely horrible debug messages.
            output = f"{output} {temp['compiler_error']}"
        if temp["program_output"] != "":
            output = f"{output} {temp['program_output']}"

        return output.strip()


class Run(commands.Cog):
    def __init__(self, bot: Tux):
        self.bot = bot
        self.run.usage = generate_usage(self.run)
        self.languages.usage = generate_usage(self.languages)
        self.services = {
            "godbolt": GodboltService(compiler_map_godbolt),
            "wandbox": WandboxService(compiler_map_wandbox),
        }

    @staticmethod
    def __remove_ansi(ansi: str) -> str:
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

    @staticmethod
    def __remove_backticks(st: str) -> str:
        """
        Removes backticks from the provided string.

        Parameters
        ----------
        st : str
            The string containing backticks.

        Returns
        -------
        str
            The string without backticks.
        """

        return ticks_re.sub("", st)

    def __parse_code(self, st: str) -> tuple[str, str]:
        cleaned_code = self.__remove_backticks(st)
        return cleaned_code.split("\n").pop(0), "\n".join(cleaned_code.splitlines()[1:])

    async def send_embedded_reply(self, ctx: commands.Context[Tux], output: str, lang: str, is_wandbox: bool) -> None:
        """
        A generalized version of an embed.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        output : str
            The output.
        lang : str
            The language of the code.
        is_wandbox: bool
            True if Wandbox is used as the backend.
        """
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="",
            description=f"{f'Service provided by {"[Wandbox](https://wandbox.org)" if is_wandbox else "[Godbolt](https://godbolt.org/)"}'}\n```{lang}\n{output}\n```",
        )

        button = discord.ui.Button(style=discord.ButtonStyle.red, label="✖ Close")  # type: ignore
        view = discord.ui.View()
        view.add_item(button)  # type: ignore

        async def button_callback(interaction: discord.Interaction):
            if interaction.message is not None:
                await interaction.message.delete()

        button.callback = button_callback

        await ctx.send(embed=embed, view=view)

    @commands.command(
        name="run",
        aliases=["compile", "exec"],
    )
    async def run(
        self,
        ctx: commands.Context[Tux],
        *,
        code: str | None,
    ):
        """
        Run code in various languages. Code should be enclosed in triple backticks.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        code : str | None
            The code to be evaluated. Provide None if the code is supposed to be grabbed from the message replied to.
        """

        # checks if the author replied to a message or not.
        if ctx.message.reference is not None and ctx.message.reference.message_id is not None:
            msg = await ctx.fetch_message(ctx.message.reference.message_id)
        else:
            msg = None

        # neither code, nor message
        if not code and not msg:
            raise commands.MissingRequiredArgument(next(iter(self.run.params.values())))

        # if there was no code, but there was a reply.
        if not code and msg:
            code = msg.content.split("```", 1)[1] if "```" in msg.content else None

        if code is None:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Fatal Exception occurred!",
                description="Bad formatting.",
            )
            await ctx.send(embed=embed)
            return

        (language, code) = self.__parse_code(code)

        await ctx.message.add_reaction("<a:BreakdancePengu:1378346831250985061>")
        is_wandbox = "wandbox" if language in compiler_map_wandbox else "godbolt"

        if language not in compiler_map_godbolt and language not in compiler_map_wandbox:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Fatal exception occurred.",
                description=f"No compiler could be found for target '{language}'.",
            )
            await ctx.message.clear_reaction("<a:BreakdancePengu:1378346831250985061>")
            await ctx.send(embed=embed)
            return

        filtered_output = await self.services[is_wandbox].run(language, code, None)

        if filtered_output is None:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Fatal exception occurred!",
                description="failed to get output from the compiler.",
            )
            await ctx.message.clear_reaction("<a:BreakdancePengu:1378346831250985061>")
            await ctx.send(embed=embed, delete_after=30)
            return

        await ctx.message.clear_reaction("<a:BreakdancePengu:1378346831250985061>")
        await self.send_embedded_reply(
            ctx,
            self.__remove_ansi(filtered_output),
            language,
            is_wandbox == "wandbox",
        )

    @commands.command(
        name="languages",
        aliases=["langs"],
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
            description="```C, C++, C#, F#, OCaml, Haskell, Julia, Python, Javascript, Typescript, Ruby, SQL, Java, Nim, Lisp, Pascal, Perl, Pony, PHP, R, Swift, Groovy, D, Bash, Rust, Kotlin```",
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Run(bot))
