from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from tux.database.controllers import DatabaseController
from tux.ui.views.config import ConfigSetChannels, ConfigSetPrivateLogs, ConfigSetPublicLogs


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseController().guild_config

    @app_commands.command(name="config_set_logs", description="Configure the guild logs.")
    async def config_set_logs(
        self,
        interaction: discord.Interaction,
        category: Literal["Public", "Private"],
    ) -> None:
        if category == "Public":
            view = ConfigSetPublicLogs()
        elif category == "Private":
            view = ConfigSetPrivateLogs()

        await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="config_set_channels", description="Configure the guild channels.")
    async def config_set_channels(
        self,
        interaction: discord.Interaction,
    ) -> None:
        view = ConfigSetChannels()
        await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="config_set_roles", description="Configure the guild roles.")
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
            app_commands.Choice(name="Perm Level 8 (e.g. Sys Admin)", value="8"),
            app_commands.Choice(name="Perm Level 9 (e.g. Bot Owner)", value="9"),
        ],
    )
    async def config_set_roles(
        self,
        interaction: discord.Interaction,
        setting: discord.app_commands.Choice[str],
        role: discord.Role,
    ) -> None:
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

    @discord.app_commands.command(name="config_get_roles", description="Get the guild roles.")
    async def config_get_roles(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            return

        embed = discord.Embed(
            title="Config - Permission Level Roles",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )

        for i in range(10):
            perm_level: str = f"perm_level_{i}_role_id"
            role_id = await self.db.get_perm_level_role(interaction.guild.id, perm_level)
            role = f"<@&{role_id}>" if role_id else "Not set"
            embed.add_field(name=f"Perm Level {i}", value=role, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Config(bot))
