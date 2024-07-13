import subprocess

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class Tldr(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def get_autocomplete(
        self,
        interaction: discord.Interaction,
        query: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Provide autocomplete suggestions for TLDR commands based on user query.

        Parameters:
        -----------
        interaction : discord.Interaction
            The interaction object where autocomplete happens.
        query : str
            Partial input from the user used to filter suggestions.

        Returns:
        --------
        List[app_commands.Choice[str]]
            A list of up to 25 command names as autocomplete choices.
        """

        # TODO: Resolve why interaction is not being used.

        commands = self.get_tldrs()

        filtered_commands = [
            app_commands.Choice(name=cmd, value=cmd) for cmd in commands if cmd.lower().startswith(query.lower())
        ]

        return filtered_commands[:25]

    @app_commands.command(name="tldr")
    @app_commands.autocomplete(command=get_autocomplete)
    async def slash_tldr(self, interaction: discord.Interaction, command: str) -> None:
        """
        Show a TLDR page for a CLI command

        Parameters:
        -----------
        interaction : discord.Interaction
            The discord interaction object.
        command : str
            The command to retrieve the TLDR page for.
        """

        tldr_page = self.get_tldr_page(command)

        embed = EmbedCreator.create_info_embed(
            title=f"TLDR for {command}",
            description=tldr_page,
            interaction=interaction,
        )

        await interaction.response.send_message(embed=embed)

        logger.info(f"{interaction.user} requested TLDR for {command}")

    @commands.command(name="tldr")
    async def prefix_tldr(self, ctx: commands.Context[commands.Bot], command: str) -> None:
        """
        Show a TLDR page for a CLI command

        Parameters:
        -----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        command : str
            The command to retrieve the TLDR page for.
        """

        tldr_page = self.get_tldr_page(command)

        embed = EmbedCreator.create_info_embed(
            title=f"TLDR for {command}",
            description=tldr_page,
            ctx=ctx,
        )

        await ctx.reply(embed=embed)

        logger.info(f"{ctx.author} requested TLDR for {command}")

    def get_tldr_page(self, command: str) -> str:
        """
        Retrieves the TLDR page for a given command.

        Parameters:
        -----------
        command : str
            The command to lookup.

        Returns:
        --------
        str
            The content of the TLDR page or an error message.
        """

        if command.startswith("-"):
            return "Invalid command: Command can't start with a dash (-)."

        return self._run_subprocess(["tldr", "-r", command], "No TLDR page found.")

    def get_tldrs(self) -> list[str]:
        """
        Fetches a list of available TLDR pages.

        Returns:
        --------
        list[str]
            List of available commands in the TLDR pages.
        """

        return self._run_subprocess(["tldr", "--list"], "No TLDR pages found.").split("\n")

    def _run_subprocess(self, command_list: list[str], default_response: str) -> str:
        """
        Helper method to run subprocesses for CLI interactions.

        Parameters:
        -----------
        command_list : list[str]
            List containing the command and its arguments.
        default_response : str
            The default response if subprocess does not output anything.

        Returns:
        --------
        str
            The stdout from the subprocess as a string, or an error message.

        Raises:
        -------
        subprocess.CalledProcessError
            If the subprocess fails to run.
        """

        try:
            process = subprocess.run(command_list, capture_output=True, text=True, check=True)

        except subprocess.CalledProcessError:
            return default_response

        else:
            return process.stdout


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tldr(bot))
