import discord
from bot import Tux
from database.controllers import DatabaseController
from discord import app_commands
from discord.ext import commands
from utils import checks


class Setup(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.config = DatabaseController().guild_config

    setup = app_commands.Group(name="setup", description="Set this bot up for your server.")

    @setup.command(name="jail")
    @commands.guild_only()
    @checks.ac_has_pl(7)
    async def setup_jail(self, interaction: discord.Interaction) -> None:
        """
        Set up the jail role channel permissions for the server.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        assert interaction.guild

        jail_role_id = await self.config.get_guild_config_field_value(interaction.guild.id, "jail_role_id")
        if not jail_role_id:
            await interaction.response.send_message("No jail role has been set up for this server.", ephemeral=True)
            return

        jail_role = interaction.guild.get_role(jail_role_id)
        if not jail_role:
            await interaction.response.send_message("The jail role has been deleted.", ephemeral=True)
            return

        jail_channel_id = await self.config.get_guild_config_field_value(interaction.guild.id, "jail_channel_id")
        if not jail_channel_id:
            await interaction.response.send_message("No jail channel has been set up for this server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        await self._set_permissions_for_channels(interaction, jail_role, jail_channel_id)

        await interaction.edit_original_response(
            content="Permissions have been set up for the jail role.",
        )

    async def _set_permissions_for_channels(
        self,
        interaction: discord.Interaction,
        jail_role: discord.Role,
        jail_channel_id: int,
    ) -> None:
        """
        Set up the permissions for the jail role in the jail channel.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        jail_role : discord.Role
            The jail role to set permissions for.
        jail_channel_id : int
            The ID of the jail channel.
        """

        assert interaction.guild

        for channel in interaction.guild.channels:
            if not isinstance(channel, discord.TextChannel | discord.VoiceChannel | discord.ForumChannel):
                continue

            if (
                jail_role in channel.overwrites
                and channel.overwrites[jail_role].send_messages is False
                and channel.overwrites[jail_role].read_messages is False
                and channel.id != jail_channel_id
            ):
                continue

            await channel.set_permissions(jail_role, send_messages=False, read_messages=False)
            if channel.id == jail_channel_id:
                await channel.set_permissions(jail_role, send_messages=True, read_messages=True)

            await interaction.edit_original_response(content=f"Setting up permissions for {channel.name}.")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Setup(bot))
