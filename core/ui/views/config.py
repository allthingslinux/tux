from typing import Any

import discord
from database.controllers import DatabaseController


class ConfigSetPrivateLogs(discord.ui.View):
    def __init__(self, *, timeout: float = 180):
        self.db = DatabaseController().guild_config
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
        if interaction.guild is None:
            return

        await self.db.update_private_log_id(interaction.guild.id, select.values[0].id)
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
        if interaction.guild is None:
            return

        await self.db.update_report_log_id(interaction.guild.id, select.values[0].id)
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

        await self.db.update_dev_log_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Dev log channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )


class ConfigSetPublicLogs(discord.ui.View):
    def __init__(self, *, timeout: float = 180):
        self.db = DatabaseController().guild_config
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

        await self.db.update_mod_log_id(interaction.guild.id, select.values[0].id)
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

        await self.db.update_audit_log_id(interaction.guild.id, select.values[0].id)
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

        await self.db.update_join_log_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"Join log channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )


class ConfigSetChannels(discord.ui.View):
    def __init__(self, *, timeout: float = 180):
        self.db = DatabaseController().guild_config
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

        await self.db.update_jail_channel_id(interaction.guild.id, select.values[0].id)
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

        await self.db.update_starboard_channel_id(interaction.guild.id, select.values[0].id)
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

        await self.db.update_general_channel_id(interaction.guild.id, select.values[0].id)
        await interaction.response.send_message(
            f"General channel set to {select.values[0]}.",
            ephemeral=True,
            delete_after=30,
        )
