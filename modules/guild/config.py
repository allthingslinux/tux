from typing import Literal

import discord
from bot import Tux
from database.controllers import DatabaseController
from discord import app_commands
from discord.ext import commands
from ui.embeds import EmbedCreator, EmbedType
from ui.views.config import ConfigSetChannels, ConfigSetPrivateLogs, ConfigSetPublicLogs
from utils.config import CONFIG

# TODO: Add onboarding setup to ensure all required channels, logs, and roles are set up
# TODO: Figure out how to handle using our custom checks because the current checks would result in a lock out
# TODO: Add a command to reset the guild config to default values


@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
class Config(commands.GroupCog, group_name="config"):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController().guild_config

    logs = app_commands.Group(name="logs", description="Configure the guild logs.")
    channels = app_commands.Group(name="channels", description="Configure the guild channels.")
    perms = app_commands.Group(name="perms", description="Configure the guild permission levels.")
    roles = app_commands.Group(name="roles", description="Configure the guild roles.")
    prefix = app_commands.Group(name="prefix", description="Configure the guild prefix.")

    @logs.command(name="set")
    @app_commands.guild_only()
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
        await interaction.response.defer(ephemeral=True)

        if category == "Public":
            view = ConfigSetPublicLogs()
        elif category == "Private":
            view = ConfigSetPrivateLogs()

        await interaction.followup.send(view=view, ephemeral=True)

    @channels.command(name="set")
    @app_commands.guild_only()
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
        await interaction.response.defer(ephemeral=True)
        view = ConfigSetChannels()
        await interaction.followup.send(view=view, ephemeral=True)

    @perms.command(name="set")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
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
    @app_commands.checks.has_permissions(administrator=True)
    async def config_set_perms(
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

        assert interaction.guild
        await interaction.response.defer(ephemeral=True)

        await self.db.update_perm_level_role(
            interaction.guild.id,
            setting.value,
            role.id,
        )

        await interaction.followup.send(
            f"Perm level {setting.value} role set to {role.mention}.",
            ephemeral=True,
        )

    @roles.command(name="set")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(setting="Which role to configure")
    @app_commands.choices(
        setting=[
            app_commands.Choice(name="Jail", value="jail_role_id"),
        ],
    )
    async def config_set_roles(
        self,
        interaction: discord.Interaction,
        setting: discord.app_commands.Choice[str],
        role: discord.Role,
    ) -> None:
        """
        Configure the guild roles.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.

        setting : discord.app_commands.Choice[str]
            The role to configure.

        role : discord.Role
            The role to set.
        """

        assert interaction.guild
        await interaction.response.defer(ephemeral=True)

        if setting.value == "jail_role_id":
            await self.db.update_jail_role_id(interaction.guild.id, role.id)
            await interaction.followup.send(
                f"{setting.value} role set to {role.mention}.",
                ephemeral=True,
            )

    @roles.command(name="get")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config_get_roles(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Get the basic roles for the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        assert interaction.guild
        await interaction.response.defer(ephemeral=True)

        embed = EmbedCreator.create_embed(
            title="Config - Roles",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
            message_timestamp=discord.utils.utcnow(),
        )

        jail_role_id = await self.db.get_jail_role_id(interaction.guild.id)
        jail_role = f"<@&{jail_role_id}>" if jail_role_id else "Not set"
        embed.add_field(name="Jail Role", value=jail_role, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @perms.command(name="get")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config_get_perms(
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

        assert interaction.guild
        await interaction.response.defer(ephemeral=True)

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
            title="Config - Permission Level Roles",
            message_timestamp=discord.utils.utcnow(),
        )

        for i in range(8):
            perm_level: str = f"perm_level_{i}_role_id"
            role_id = await self.db.get_perm_level_role(interaction.guild.id, perm_level)
            role = f"<@&{role_id}>" if role_id else "Not set"
            embed.add_field(name=f"Perm Level {i}", value=role, inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @channels.command(name="get")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config_get_channels(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Get the channels for each category.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        assert interaction.guild
        await interaction.response.defer(ephemeral=True)

        embed = EmbedCreator.create_embed(
            title="Config - Channels",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
            message_timestamp=discord.utils.utcnow(),
        )

        jail_channel_id = await self.db.get_jail_channel_id(interaction.guild.id)
        jail_channel = f"<#{jail_channel_id}>" if jail_channel_id else "Not set"
        embed.add_field(name="Jail Channel", value=jail_channel, inline=False)

        starboard_channel_id = await self.db.get_starboard_channel_id(interaction.guild.id)
        starboard_channel = f"<#{starboard_channel_id}>" if starboard_channel_id else "Not set"
        embed.add_field(name="Starboard Channel", value=starboard_channel, inline=False)

        general_channel_id = await self.db.get_general_channel_id(interaction.guild.id)
        general_channel = f"<#{general_channel_id}>" if general_channel_id else "Not set"
        embed.add_field(name="General Channel", value=general_channel, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @logs.command(name="get")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config_get_logs(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Get the log channels for every category.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        assert interaction.guild
        await interaction.response.defer(ephemeral=True)

        embed = EmbedCreator.create_embed(
            title="Config - Logs",
            embed_type=EmbedType.INFO,
            custom_color=discord.Color.blue(),
            message_timestamp=discord.utils.utcnow(),
        )

        join_log_id = await self.db.get_join_log_id(interaction.guild.id)
        join_log = f"<#{join_log_id}>" if join_log_id else "Not set"
        embed.add_field(name="Join Log", value=join_log, inline=True)

        audit_log_id = await self.db.get_audit_log_id(interaction.guild.id)
        audit_log = f"<#{audit_log_id}>" if audit_log_id else "Not set"
        embed.add_field(name="Audit Log", value=audit_log, inline=True)

        mod_log_id = await self.db.get_mod_log_id(interaction.guild.id)
        mod_log = f"<#{mod_log_id}>" if mod_log_id else "Not set"
        embed.add_field(name="Mod Log", value=mod_log, inline=True)

        private_log_id = await self.db.get_private_log_id(interaction.guild.id)
        private_log = f"<#{private_log_id}>" if private_log_id else "Not set"
        embed.add_field(name="Private Log", value=private_log, inline=True)

        report_log_id = await self.db.get_report_log_id(interaction.guild.id)
        report_log = f"<#{report_log_id}>" if report_log_id else "Not set"
        embed.add_field(name="Report Log", value=report_log, inline=True)

        dev_log_id = await self.db.get_dev_log_id(interaction.guild.id)
        dev_log = f"<#{dev_log_id}>" if dev_log_id else "Not set"
        embed.add_field(name="Dev Log", value=dev_log, inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @prefix.command(name="set")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config_set_prefix(
        self,
        interaction: discord.Interaction,
        prefix: app_commands.Range[str, 1, 10],
    ) -> None:
        """
        Set the prefix for the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        prefix : str
            The prefix to set for the guild.
        """

        assert interaction.guild
        await interaction.response.defer(ephemeral=True)

        await self.db.update_guild_prefix(interaction.guild.id, prefix)

        await interaction.followup.send(
            embed=EmbedCreator.create_embed(
                bot=self.bot,
                user_name=interaction.user.name,
                user_display_avatar=interaction.user.display_avatar.url,
                embed_type=EmbedCreator.SUCCESS,
                title="Guild Config",
                description=f"The prefix was updated to `{prefix}`",
            ),
        )

    @prefix.command(name="clear")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config_clear_prefix(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Reset the prefix to the default value for this guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        assert interaction.guild
        await interaction.response.defer(ephemeral=True)

        await self.db.delete_guild_prefix(interaction.guild.id)

        await interaction.followup.send(
            embed=EmbedCreator.create_embed(
                bot=self.bot,
                user_name=interaction.user.name,
                user_display_avatar=interaction.user.display_avatar.url,
                embed_type=EmbedCreator.SUCCESS,
                title="Guild Config",
                description=f"The prefix was reset to `{CONFIG.DEFAULT_PREFIX}`",
            ),
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Config(bot))
