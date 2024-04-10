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
        if len(result) > 25:
            return result[:25]
        return result

    @app_commands.command(name="tldr", description="Show a tldr page for (almost) any cli command")
    @app_commands.describe(command="which command to show")
    @app_commands.autocomplete(command=get_autocomplete)
    async def tldr(self, interaction: discord.Interaction, command: str) -> None:
        logger.info(f"{interaction.user} used the /tldr to show info about {command}")
        tldr_page = self.get_tldr_page(command)
        embed = EmbedCreator.create_default_embed(
            title=f"TLDR for {command}", description=tldr_page, interaction=interaction
        )
        await interaction.response.send_message(embed=embed)

    # please change this as it might be vulnerable
    def get_tldr_page(self, command: str) -> str:
        # So yeah, this uses tldr cli on host machine to get tldr page
        # and return it, if somehow an error occurs it will return
        # An error occured
        if command.startswith("-"):
            return "Can't run tldr: `command can't start with a dash (-)`"
        proc = subprocess.Popen(
            ["tldr", "-r", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # shell=True,
        )
        (out, err) = proc.communicate()
        if not err:
            if len(out) < 1:
                return "No tldr page found"
            return out.decode()
        return f"An error occured: {err.decode()}"

    def get_tldrs(self) -> list[str]:
        proc = subprocess.Popen(["tldr", "--list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        if err:
            return [err.decode()]
        return out.decode().split("\n")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tldr(bot))
