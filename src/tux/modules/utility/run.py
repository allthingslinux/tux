"""
Code execution cog for running code snippets in various programming languages.

This module provides functionality to execute code using external services
like Godbolt and Wandbox, with support for multiple programming languages
and proper error handling through custom exceptions.
"""

import re
from abc import ABC, abstractmethod
from contextlib import suppress

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.wrappers import godbolt, wandbox
from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
    TuxCompilationError,
    TuxInvalidCodeFormatError,
    TuxMissingCodeError,
    TuxUnsupportedLanguageError,
)
from tux.ui.embeds import EmbedCreator

# Constants
ANSI_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
BACKTICKS_PATTERN = re.compile(r"```")

# Compiler mappings
GODBOLT_COMPILERS = {
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

WANDBOX_COMPILERS = {
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

SUPPORTED_LANGUAGES = [
    "C",
    "C++",
    "C#",
    "F#",
    "OCaml",
    "Haskell",
    "Julia",
    "Python",
    "Javascript",
    "Typescript",
    "Ruby",
    "SQL",
    "Java",
    "Nim",
    "Lisp",
    "Pascal",
    "Perl",
    "Pony",
    "PHP",
    "R",
    "Swift",
    "Groovy",
    "D",
    "Bash",
    "Rust",
    "Kotlin",
]

SERVICE_LINKS = {
    "wandbox": f"[Wandbox]({wandbox.url.split('/api')[0]})",
    "godbolt": f"[Godbolt]({godbolt.url})",
}


def _remove_ansi(text: str) -> str:
    """
    Remove ANSI escape sequences from text.

    Parameters
    ----------
    text : str
        Text containing ANSI escape sequences.

    Returns
    -------
    str
        Text with ANSI sequences removed.
    """
    return ANSI_PATTERN.sub("", text)


def _remove_backticks(text: str) -> str:
    """
    Remove backticks from text.

    Parameters
    ----------
    text : str
        Text containing backticks.

    Returns
    -------
    str
        Text with backticks removed.
    """
    return BACKTICKS_PATTERN.sub("", text)


class CodeDispatch(ABC):
    """Abstract base class for code execution services."""

    def __init__(self, compiler_map: dict[str, str]) -> None:
        """
        Initialize the code dispatch service.

        Parameters
        ----------
        compiler_map : dict[str, str]
            Mapping of language names to compiler identifiers.
        """
        self.compiler_map = compiler_map

    async def run(
        self,
        language: str,
        code: str,
        options: str | None = None,
    ) -> str | None:
        """
        Execute code using the appropriate compiler.

        Parameters
        ----------
        language : str
            The programming language identifier.
        code : str
            The source code to execute.
        options : str | None, optional
            Additional compiler options. Defaults to None.

        Returns
        -------
        str | None
            The execution output or None if execution failed.
        """
        compiler = self.compiler_map.get(language)
        if compiler is None:
            return None
        return await self._execute(compiler, code, options)

    @abstractmethod
    async def _execute(
        self,
        compiler: str,
        code: str,
        options: str | None,
    ) -> str | None:
        """
        Execute code with the specified compiler.

        Parameters
        ----------
        compiler : str
            The compiler identifier.
        code : str
            The source code to execute.
        options : str | None
            Additional compiler options.

        Returns
        -------
        str | None
            The execution output or None if execution failed.
        """


class GodboltService(CodeDispatch):
    """Code execution service using Godbolt compiler explorer."""

    async def _execute(
        self,
        compiler: str,
        code: str,
        options: str | None,
    ) -> str | None:
        """
        Execute code using Godbolt service.

        Parameters
        ----------
        compiler : str
            The Godbolt compiler identifier.
        code : str
            The source code to compile and execute.
        options : str | None
            Additional compiler options. C++ options are automatically enhanced.

        Returns
        -------
        str | None
            The execution output with header lines removed, or None if execution failed.
        """
        try:
            output = await godbolt.getoutput(code, compiler, options)
        except (
            TuxAPIConnectionError,
            TuxAPIRequestError,
            TuxAPIResourceNotFoundError,
        ) as e:
            logger.warning(f"Godbolt API error for compiler {compiler}: {e}")
            return None

        if not output:
            logger.debug(f"Godbolt returned no output for compiler {compiler}")
            return None

        # Remove header lines (first 5 lines)
        lines = output.split("\n")
        result = "\n".join(lines[5:])
        logger.debug(
            f"Godbolt execution completed (output length: {len(result)} chars)",
        )
        return result


class WandboxService(CodeDispatch):
    """Code execution service using Wandbox online compiler."""

    async def _execute(
        self,
        compiler: str,
        code: str,
        options: str | None,
    ) -> str | None:
        """
        Execute code using Wandbox service.

        Parameters
        ----------
        compiler : str
            The Wandbox compiler identifier.
        code : str
            The source code to compile and execute.
        options : str | None
            Additional compiler options.

        Returns
        -------
        str | None
            Combined compiler errors and program output, or None if execution failed.

        Notes
        -----
        Nim compiler errors are filtered out due to excessive verbosity.
        """
        try:
            result = await wandbox.getoutput(code, compiler, options)
        except (
            TuxAPIConnectionError,
            TuxAPIRequestError,
            TuxAPIResourceNotFoundError,
        ) as e:
            logger.warning(f"Wandbox API error for compiler {compiler}: {e}")
            return None

        if not result:
            logger.debug(f"Wandbox returned no output for compiler {compiler}")
            return None

        logger.debug(f"Wandbox execution received result for compiler {compiler}")
        output_parts: list[str] = []

        # Handle compiler errors (skip for Nim due to verbose debug messages)
        if (
            compiler_error := result.get("compiler_error")
        ) and compiler != self.compiler_map.get("nim"):
            output_parts.append(str(compiler_error))

        if program_error := result.get("program_error"):
            output_parts.append(str(program_error))

        # Handle program output
        if program_output := result.get("program_output"):
            output_parts.append(str(program_output))

        return " ".join(output_parts).strip() if output_parts else None


class Run(BaseCog):
    """
    Cog for executing code in various programming languages.

    Supports multiple programming languages through Godbolt and Wandbox services.
    Provides code execution with proper error handling and user-friendly output.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Run cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        # Usage is auto-generated by BaseCog
        self.services = {
            "godbolt": GodboltService(GODBOLT_COMPILERS),
            "wandbox": WandboxService(WANDBOX_COMPILERS),
        }

    def _parse_code_block(self, text: str) -> tuple[str, str]:
        """
        Parse a code block to extract language and code.

        Parameters
        ----------
        text : str
            The code block text.

        Returns
        -------
        tuple[str, str]
            A tuple containing (language, code).
        """
        cleaned_text = _remove_backticks(text)
        lines = cleaned_text.split("\n")
        language = lines[0] if lines else ""
        code = "\n".join(lines[1:]) if len(lines) > 1 else ""
        return language, code

    def _determine_service(self, language: str) -> str | None:
        """
        Determine which service to use for a given language.

        Parameters
        ----------
        language : str
            The programming language identifier.

        Returns
        -------
        str | None
            The service name ("wandbox" or "godbolt") or None if language is not supported.
        """
        # sourcery skip: assign-if-exp, reintroduce-else
        if language in WANDBOX_COMPILERS:
            return "wandbox"
        if language in GODBOLT_COMPILERS:
            return "godbolt"
        return None

    async def _create_result_embed(
        self,
        ctx: commands.Context[Tux],
        output: str,
        language: str,
        service: str,
    ) -> discord.Embed:
        """
        Create a result embed for code execution output.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        output : str
            The execution output.
        language : str
            The programming language.
        service : str
            The service used for execution.

        Returns
        -------
        discord.Embed
            The created embed.
        """
        service_link = SERVICE_LINKS.get(service, service)

        description = f"-# Service provided by {service_link}\n```{language}\n{output or 'no result to show.'}\n```"

        return EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="",
            description=description,
        )

    def _create_close_button_view(self) -> discord.ui.View:
        """
        Create a view with a close button.

        Returns
        -------
        discord.ui.View
            The view with close button.
        """

        async def close_callback(interaction: discord.Interaction) -> None:
            """Handle the close button callback to delete the message."""
            if interaction.message:
                await interaction.message.delete()

        button = discord.ui.Button[discord.ui.View](
            style=discord.ButtonStyle.red,
            label="✖ Close",
        )
        button.callback = close_callback

        view = discord.ui.View()
        view.add_item(button)
        return view

    async def _extract_code_from_message(
        self,
        ctx: commands.Context[Tux],
        code: str | None,
    ) -> str | None:
        """
        Extract code from the command or referenced message.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        code : str | None
            Code provided directly in the command.

        Returns
        -------
        str | None
            The extracted code or None if not found.

        Notes
        -----
        If no code is provided directly, attempts to extract code from
        a replied-to message containing triple backticks.
        """
        if code:
            return code

        # Check for replied message
        if ctx.message.reference and ctx.message.reference.message_id:
            with suppress(discord.NotFound):
                referenced_message = await ctx.fetch_message(
                    ctx.message.reference.message_id,
                )
                if "```" in referenced_message.content:
                    return referenced_message.content.split("```", 1)[1]

        return None

    @commands.command(name="run", aliases=["compile", "exec"])
    async def run(self, ctx: commands.Context[Tux], *, code: str | None = None) -> None:
        """
        Execute code in various programming languages.

        Code should be enclosed in triple backticks with language specification.
        You can also reply to a message containing code to execute it.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        code : str | None, optional
            The code to execute, or None to use referenced message. Defaults to None.

        Raises
        ------
        TuxMissingCodeError
            When no code is provided and no replied message contains code.
        TuxInvalidCodeFormatError
            When the code format is invalid or missing language specification.
        TuxUnsupportedLanguageError
            When the specified language is not supported.
        TuxCompilationError
            When code compilation or execution fails.
        """
        # Extract code from command or referenced message
        extracted_code = await self._extract_code_from_message(ctx, code)

        if not extracted_code:
            logger.debug(f"No code provided by {ctx.author.id} for run command")
            raise TuxMissingCodeError

        # Parse the code block
        language, source_code = self._parse_code_block(extracted_code)

        if not language or not source_code.strip():
            logger.debug(f"Invalid code format from {ctx.author.id}")
            raise TuxInvalidCodeFormatError

        # Determine service to use
        service = self._determine_service(language)
        if not service:
            logger.warning(
                f"Unsupported language '{language}' requested by {ctx.author.name} ({ctx.author.id})",
            )
            raise TuxUnsupportedLanguageError(language, SUPPORTED_LANGUAGES)

        logger.info(
            f"🔨 Code execution request: {language} via {service} from {ctx.author.name} ({ctx.author.id})",
        )

        # Execute the code
        logger.debug(
            f"Executing {language} code (length: {len(source_code)} chars) via {service}",
        )
        output = await self.services[service].run(language, source_code)

        if output is None:
            logger.warning(
                f"Code execution failed (no output) for {language} from {ctx.author.id}",
            )
            raise TuxCompilationError

        # Create and send result embed
        cleaned_output = _remove_ansi(output)
        result_embed = await self._create_result_embed(
            ctx,
            cleaned_output,
            language,
            service,
        )
        view = self._create_close_button_view()

        await ctx.send(embed=result_embed, view=view)
        logger.info(
            f"Code execution successful: {language} for {ctx.author.name} ({ctx.author.id})",
        )

    @commands.command(name="languages", aliases=["langs", "lang"])
    async def languages(self, ctx: commands.Context[Tux]) -> None:
        """
        Display all supported programming languages to use with the `run` command.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        """
        languages_text = ", ".join(SUPPORTED_LANGUAGES)

        help_text = (
            "The following languages are currently supported by the `run` command:\n"
            f"```{languages_text}\n```\n\n"
            "Please use triple backticks and provide syntax highlighting like below:\n"
            '```\n`\u200b``python\nprint("Hello, World!")\n`\u200b``\n```\n'
        )

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Supported Languages",
            description=help_text,
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Set up the Run cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Run(bot))
