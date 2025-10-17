"""
Discord Configuration Views for Tux Bot.

This module provides Discord UI views for configuring bot settings,
including private log channels and report log channels.
"""

from typing import Any

import discord

from tux.database.controllers import DatabaseCoordinator
from tux.database.service import DatabaseService
from tux.database.utils import get_db_controller_from


class ConfigSetPrivateLogs(discord.ui.View):
    """View for configuring private log channels."""

    def __init__(self, *, timeout: float = 180, bot: Any | None = None, db_service: DatabaseService | None = None):
        """Initialize the config view for private logs.

        Parameters
        ----------
        timeout : float, optional
            View timeout in seconds, by default 180.
        bot : Any, optional
            Bot instance for database access, by default None.
        db_service : DatabaseService, optional
            Direct database service instance, by default None.
        """
        if db_service is not None:
            # If we have a DatabaseService, create a coordinator from it

            self.db: DatabaseCoordinator = DatabaseCoordinator(db_service)
        elif bot is not None:
            # Get the database coordinator
            db_controller = get_db_controller_from(bot)
            if db_controller is None:
                message = "DatabaseCoordinator not available. DI is required for ConfigSetPrivateLogs."
                raise RuntimeError(message)
            self.db = db_controller
        else:
            message = "DatabaseCoordinator not available. DI is required for ConfigSetPrivateLogs."
            raise RuntimeError(message)
        super().__init__(timeout=timeout)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the private log channel.",
    )
    async def _set_private_log(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        """Set the private log channel for the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered this action.
        select : discord.ui.ChannelSelect[Any]
            The channel select component.
        """
        if interaction.guild is None:
            return

        await self.db.guild_config.update_private_log_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Private log channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the report log channel.",
    )
    async def _set_report_log(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        """Set the report log channel for the guild.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered this action.
        select : discord.ui.ChannelSelect[Any]
            The channel select component.
        """
        if interaction.guild is None:
            return

        await self.db.guild_config.update_report_log_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Report log channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the dev log channel.",
    )
    async def _set_dev_log(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        if interaction.guild is None:
            return

        await self.db.guild_config.update_dev_log_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Dev log channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )


class ConfigSetPublicLogs(discord.ui.View):
    def __init__(self, *, timeout: float = 180, bot: Any | None = None, db_service: DatabaseService | None = None):
        if db_service is not None:
            # If we have a DatabaseService, create a coordinator from it

            self.db: DatabaseCoordinator = DatabaseCoordinator(db_service)
        elif bot is not None:
            # Get the database coordinator
            db_controller = get_db_controller_from(bot)
            if db_controller is None:
                message = "DatabaseCoordinator not available. DI is required for ConfigSetPublicLogs."
                raise RuntimeError(message)
            self.db = db_controller
        else:
            message = "DatabaseCoordinator not available. DI is required for ConfigSetPublicLogs."
            raise RuntimeError(message)
        super().__init__(timeout=timeout)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the mod log channel.",
    )
    async def _set_mod_log(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        if interaction.guild is None:
            return

        await self.db.guild_config.update_mod_log_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Mod log channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the audit log channel.",
    )
    async def _set_audit_log(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        if interaction.guild is None:
            return

        await self.db.guild_config.update_audit_log_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Audit log channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the join log channel.",
    )
    async def _set_join_log(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        if interaction.guild is None:
            return

        await self.db.guild_config.update_join_log_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Join log channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )


class ConfigSetChannels(discord.ui.View):
    def __init__(self, *, timeout: float = 180, bot: Any | None = None, db_service: DatabaseService | None = None):
        if db_service is not None:
            # If we have a DatabaseService, create a coordinator from it

            self.db: DatabaseCoordinator = DatabaseCoordinator(db_service)
        elif bot is not None:
            # Get the database coordinator
            db_controller = get_db_controller_from(bot)
            if db_controller is None:
                message = "DatabaseCoordinator not available. DI is required for ConfigSetChannels."
                raise RuntimeError(message)
            self.db = db_controller
        else:
            message = "DatabaseCoordinator not available. DI is required for ConfigSetChannels."
            raise RuntimeError(message)
        super().__init__(timeout=timeout)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the jail channel.",
    )
    async def _set_jail_channel(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        if interaction.guild is None:
            return

        await self.db.guild_config.update_jail_channel_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Jail channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the starboard channel.",
    )
    async def _set_starboard_channel(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        if interaction.guild is None:
            return

        await self.db.guild_config.update_starboard_channel_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Starboard channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Set the general channel.",
    )
    async def _set_general_channel(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect[Any],
    ) -> None:
        if interaction.guild is None:
            return

        await self.db.guild_config.update_general_channel_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"General channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )
