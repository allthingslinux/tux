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
        self, interaction: discord.Interaction, query: str
    ) -> list[app_commands.Choice[str]]:
        commands = self.get_tldrs()
        result = [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in commands
            if cmd.lower().startswith(query.lower())
        ]
        return result[:25] if len(result) > 25 else result

    @app_commands.command(name="tldr", description="Show a tldr page for (almost) any cli command")
    @app_commands.describe(command="which command to show")
    @app_commands.autocomplete(command=get_autocomplete)
    async def tldr(self, interaction: discord.Interaction, command: str) -> None:
        logger.info(f"{interaction.user} used the /tldr to show info about {command}")
        tldr_page = self.get_tldr_page(command)
        embed = EmbedCreator.create_info_embed(
            title=f"TLDR for {command}", description=tldr_page, interaction=interaction
        )
        await interaction.response.send_message(embed=embed)

    def get_tldr_page(self, command: str) -> str:
        if command.startswith("-"):
            return "Can't run tldr: `command can't start with a dash (-)`"
        return self._run_subprocess(["tldr", "-r", command], "No tldr page found")

    def get_tldrs(self) -> list[str]:
        return self._run_subprocess(["tldr", "--list"], "No tldr pages found").split("\n")

    def _run_subprocess(self, command_list: list[str], default_response: str) -> str:
        try:
            proc = subprocess.Popen(
                command_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (out, err) = proc.communicate()
            if not err:
                return default_response if len(out) < 1 else out.decode()

            logger.error(f"An error occured during subprocess: {err.decode()}")
            return "An error occurred"  # noqa: TRY300

        except Exception as e:
            logger.error(f"An error occurred: {e!s}")
            return "An error occurred"


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tldr(bot))
