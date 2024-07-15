import discord
from discord import app_commands
from discord.ext import commands


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    role = app_commands.Group(name="roles", description="Role commands.")

    @app_commands.checks.has_any_role("Admin")
    @role.command(name="create", description="Creates a role in the guild.")
    async def create(self, interaction: discord.Interaction, name: str) -> None:
        """
        Creates a role in the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        name : str
            The name of the role to create.
        """

        if interaction.guild is not None:
            role = await interaction.guild.create_role(name=name)

            await interaction.response.send_message(f"Created role {role.name}.")

    @app_commands.checks.has_any_role("Admin")
    @role.command(name="delete", description="Deletes a role in the guild.")
    async def delete(self, interaction: discord.Interaction, role: discord.Role) -> None:
        """
        Deletes a role in the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        role : discord.Role
            The role to delete.
        """

        await role.delete()

        await interaction.response.send_message(f"Deleted role {role.name}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roles(bot))
