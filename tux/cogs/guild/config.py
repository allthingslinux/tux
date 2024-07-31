from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from tux.database.controllers import DatabaseController
from tux.ui.views.config import ConfigSetChannels, ConfigSetPrivateLogs, ConfigSetPublicLogs

# TODO: Add onboarding setup to ensure all required channels, logs, and roles are set up
# TODO: Figure out how to handle using our custom checks because the current checks would result in a lock out
# TODO: Add a command to reset the guild config to default values


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseController().guild_config

    @app_commands.command(name="config_set_logs")
    @app_commands.describe(setting="Which category of logs to configure")
    @app_commands.guild_only()
    # @checks.ac_has_pl(7)
    @app_commands.checks.has_permissions(administrator=True)
    async def config_set_logs(
        self,
        interaction: discord.Interaction,
        category: Literal["Public", "Private"],
    ) -> None:
        """
        Configure the guild logs.

        Parameters
        ----------

        interaction : discord.Interaction
            The discord interaction object.
        category : Literal["Public", "Private"]
            The category of logs to configure.
        """

        if category == "Public":
            view = ConfigSetPublicLogs()
        elif category == "Private":
            view = ConfigSetPrivateLogs()

        await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="config_set_channels")
    @app_commands.guild_only()
    # @checks.ac_has_pl(7)
    @app_commands.checks.has_permissions(administrator=True)
    async def config_set_channels(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Configure the guild channels.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        view = ConfigSetChannels()
        await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="config_set_roles")
    @app_commands.describe(setting="Which permission level to configure")
    @app_commands.choices(
        setting=[
            app_commands.Choice(name="Perm Level 0 (e.g. Member)", value="0"),
            app_commands.Choice(name="Perm Level 1 (e.g. Support)", value="1"),
            app_commands.Choice(name="Perm Level 2 (e.g. Junior Mod)", value="2"),
            app_commands.Choice(name="Perm Level 3 (e.g. Mod)", value="3"),
            app_commands.Choice(name="Perm Level 4 (e.g. Senior Mod)", value="4"),
            app_commands.Choice(name="Perm Level 5 (e.g. Admin)", value="5"),
            app_commands.Choice(name="Perm Level 6 (e.g. Head Admin)", value="6"),
            app_commands.Choice(name="Perm Level 7 (e.g. Server Owner)", value="7"),
        ],
    )
    @app_commands.guild_only()
    # @checks.ac_has_pl(7)
    @app_commands.checks.has_permissions(administrator=True)
    async def config_set_roles(
        self,
        interaction: discord.Interaction,
        setting: discord.app_commands.Choice[str],
        role: discord.Role,
    ) -> None:
        """
        Set the role for a permission level.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        setting : discord.app_commands.Choice[str]
            The permission level to configure.
        role : discord.Role
            The role to set for the permission level.
        """

        if interaction.guild is None:
            return

        await self.db.update_perm_level_role(
            interaction.guild.id,
            setting.value,
            role.id,
        )

        await interaction.response.send_message(
            f"Perm level {setting.value} role set to {role.mention}.",
            ephemeral=True,
        )

    @app_commands.command(name="config_get_roles")
    @app_commands.guild_only()
    # @checks.ac_has_pl(7)
    @app_commands.checks.has_permissions(administrator=True)
    async def config_get_roles(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Get the roles for each permission level.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        if interaction.guild is None:
            return

        embed = discord.Embed(
            title="Config - Permission Level Roles",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )

        for i in range(8):
            perm_level: str = f"perm_level_{i}_role_id"
            role_id = await self.db.get_perm_level_role(interaction.guild.id, perm_level)
            role = f"<@&{role_id}>" if role_id else "Not set"
            embed.add_field(name=f"Perm Level {i}", value=role, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Config(bot))
