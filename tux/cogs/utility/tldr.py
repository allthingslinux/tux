import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class Tldr(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="tldr", description="Show a tldr page for (almost) any cli command")
    @app_commands.describe(command="which command to show")
    async def tldr(self, interaction: discord.Interaction, command: str) -> None:
        logger.info(f"{interaction.user} used the /tldr to show info about {command}")
        tldr_page = self.get_tldr_page(command)
        embed = EmbedCreator.create_default_embed(
            title=f"TLDR for {command}", description=tldr_page, interaction=interaction
        )
        await interaction.response.send_message(embed=embed)

    # please change this as it might be vulnerable
    def get_tldr_page(self, command: str) -> str:
        import subprocess

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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tldr(bot))
