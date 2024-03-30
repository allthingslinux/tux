import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    group = app_commands.Group(name="roles", description="Role commands.")

    @group.command(name="delete", description="Deletes a role in the guild.")
    async def delete(self, interaction: discord.Interaction, role: discord.Role) -> None:
        await role.delete()
        await interaction.response.send_message(f"Deleted role {role.name}.")
        logger.info(f"{interaction.user} deleted role {role.name}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roles(bot))
