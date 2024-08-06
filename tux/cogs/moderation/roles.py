import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils import checks


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    roles = app_commands.Group(name="roles", description="Commands for managing roles.")

    @roles.command(name="toggle")
    @app_commands.guild_only()
    @checks.ac_has_pl(3)
    async def toggle_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role) -> None:
        """
        Toggle a role for a user.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        user : discord.Member
            The user to toggle the role for.
        role : discord.Role
            The role to toggle.
        """

        if role in user.roles:
            await user.remove_roles(role)
            await interaction.response.send_message(
                f"Removed role {role.mention} from {user.mention}",
                allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=True,
                delete_after=30,
            )
            logger.info(f"{interaction.user} removed role {role.name} from {user}.")
        else:
            await user.add_roles(role)
            await interaction.response.send_message(
                f"Added role {role.mention} to {user.mention}",
                allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=True,
                delete_after=30,
            )
            logger.info(f"{interaction.user} added role {role.name} to {user}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roles(bot))
