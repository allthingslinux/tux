import datetime
from typing import Any

import discord
from discord.ext import commands

from tux.database.controllers import DatabaseController
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator
from tux.utils.functions import compare_changes, compare_guild_channel_changes, extract_guild_attrs


class AuditLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_controller = DatabaseController()
        self.audit_log_channel_id: int = CONST.LOG_CHANNELS["AUDIT"]
        self.dev_log_channel_id: int = CONST.LOG_CHANNELS["DEV"]

    async def send_to_audit_log(self, embed: discord.Embed) -> None:
        channel = self.bot.get_channel(self.audit_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    async def send_to_dev_log(self, embed: discord.Embed) -> None:
        channel = self.bot.get_channel(self.dev_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    """Audit Logging - Channel"""

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """
        Logs when a channel is created in a guild.

        Parameters
        ----------
        channel : discord.abc.GuildChannel
            The channel that was created.
        """

        audit_embed = EmbedCreator.create_log_embed(
            title="Channel Created",
            description=f"A new channel was created in {channel.guild.name}",
        )

        audit_embed.add_field(name="Channel Name", value=channel.name)
        audit_embed.add_field(name="Channel ID", value=f"`{channel.id}`")
        audit_embed.add_field(name="Channel Type", value=channel.type)

        await self.send_to_audit_log(audit_embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """
        Logs when a channel is deleted in a guild.

        Parameters
        ----------
        channel : discord.abc.GuildChannel
            The channel that was deleted.
        """

        audit_embed = EmbedCreator.create_log_embed(
            title="Channel Deleted",
            description=f"A channel was deleted in {channel.guild.name}",
        )

        audit_embed.add_field(name="Channel Name", value=channel.name)
        audit_embed.add_field(name="Channel ID", value=f"`{channel.id}`")
        audit_embed.add_field(name="Channel Type", value=channel.type)

        await self.send_to_audit_log(audit_embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel,
    ) -> None:
        """
        Logs when a channel is updated in a guild.

        Parameters
        ----------
        before : discord.abc.GuildChannel
            The channel before the update.
        after : discord.abc.GuildChannel
            The channel after the update.
        """

        audit_embed = EmbedCreator.create_log_embed(
            title="Channel Updated",
            description=f"A channel was updated in {before.guild.name}",
        )

        changes = compare_guild_channel_changes(before, after)

        for change in changes:
            audit_embed.add_field(name="Change", value=f"`{change}`")

        await self.send_to_audit_log(audit_embed)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(
        self,
        channel: discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel,
        last_pin: datetime.datetime | None,
    ) -> None:
        """
        Logs when a message is pinned or unpinned in a channel.

        Parameters
        ----------
        channel : discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel
            The channel in which the message was pinned/unpinned.
        last_pin : datetime.datetime | None
            The time of the last pin.
        """

        if isinstance(channel, discord.abc.GuildChannel | discord.Thread):
            channel_name = channel.mention
        else:
            channel_name = "Private Channel"
        channel_id = channel.id

        embed = EmbedCreator.create_log_embed(
            title="Channel Pins Update",
            description="A message was pinned/unpinned in a channel",
        )

        embed.add_field(name="Channel", value=f"{channel_name} (`{channel_id}`)")

        if isinstance(channel, discord.TextChannel | discord.Thread):
            pins = await channel.pins()
            if pins:
                embed.add_field(name="Latest pin", value=f"[Jump to message]({pins[0].jump_url})")

        await self.send_to_audit_log(embed)

    """Audit logging - Guild"""

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        """
        Logs when a guild is updated.

        Parameters
        ----------
        before : discord.Guild
            The guild before the update.
        after : discord.Guild
            The guild after the update.
        """

        before_attrs: dict[str, Any] = extract_guild_attrs(before)
        after_attrs: dict[str, Any] = extract_guild_attrs(after)

        embed = EmbedCreator.create_log_embed(title="Guild Updated", description="Before and after")

        if changes := compare_changes(before_attrs, after_attrs):
            embed.add_field(name="Changes", value="\n".join(changes).upper(), inline=False)

        await self.send_to_audit_log(embed)

    """Audit logging - Emoji and Stickers"""

    @commands.Cog.listener()
    async def on_guild_emojis_update(
        self,
        guild: discord.Guild,
        before: list[discord.Emoji],
        after: list[discord.Emoji],
    ) -> None:
        """
        Logs when emojis are updated in a guild.

        Parameters
        ----------
        guild : discord.Guild
            The guild where the emojis were updated.
        before : list[discord.Emoji]
            The list of emojis before the update.
        after : list[discord.Emoji]
            The list of emojis after the update.
        """

        embed = EmbedCreator.create_log_embed(
            title="Guild Emojis Updated",
            description=f"Emojis: {len(before)} -> {len(after)}",
        )

        new_emoji = [emoji for emoji in after if emoji not in before]
        deleted_emoji = [emoji for emoji in before if emoji not in after]

        if new_emoji:
            emojis_str = " ".join([str(emoji) for emoji in new_emoji])
            embed.add_field(name="Added emoji", value=emojis_str[:1024])

        if deleted_emoji:
            emojis_str = ", ".join([emoji.name for emoji in deleted_emoji])
            embed.add_field(name="Deleted Emoji", value=emojis_str[:1024])

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(
        self,
        guild: discord.Guild,
        before: list[discord.Sticker],
        after: list[discord.Sticker],
    ) -> None:
        """
        Logs when stickers are updated in a guild.

        Parameters
        ----------
        guild : discord.Guild
            The guild where the stickers were updated.
        before : list[discord.Sticker]
            The list of stickers before the update.
        after : list[discord.Sticker]
            The list of stickers after the update.
        """

        embed = discord.Embed(
            title="Guild Stickers Updated",
            description=f"Stickers: {len(before)} -> {len(after)}",
        )

        new_stickers = [sticker for sticker in after if sticker not in before]
        deleted_stickers = [sticker for sticker in before if sticker not in after]

        if new_stickers:
            stickers_str = "\n".join(
                [f"[{sticker.name}]({sticker.url})" for sticker in new_stickers],
            )
            embed.add_field(name="Added Stickers", value=stickers_str[:1024])

            embed.set_image(url=new_stickers[0].url)

        if deleted_stickers:
            stickers_str = ", ".join([sticker.name for sticker in deleted_stickers])
            embed.add_field(name="Deleted Stickers", value=stickers_str[:1024])

        await self.send_to_audit_log(embed)

    """Audit Logging - Integrations"""

    @commands.Cog.listener()
    async def on_integration_create(self, integration: discord.Integration) -> None:
        """
        Logs when an integration is created.

        Parameters
        ----------
        integration : discord.Integration
            The integration that was created.
        """

        embed = EmbedCreator.create_log_embed(
            title="Integration Created",
            description=f"Integration: {integration.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_integration_update(self, integration: discord.Integration) -> None:
        """
        Logs when an integration is updated.

        Parameters
        ----------
        integration : discord.Integration
            The integration that was updated.
        """

        embed = EmbedCreator.create_log_embed(
            title="Integration Updated",
            description=f"Integration: {integration.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_integration_delete(self, integration: discord.Integration) -> None:
        """
        Logs when an integration is deleted.

        Parameters
        ----------
        integration : discord.Integration
            The integration that was deleted.
        """

        embed = EmbedCreator.create_log_embed(
            title="Integration Deleted",
            description=f"Integration: {integration.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel) -> None:
        """
        Logs when webhooks are updated in a channel.

        Parameters
        ----------
        channel : discord.TextChannel
            The channel where the webhooks were updated.
        """

        embed = EmbedCreator.create_log_embed(
            title="Webhooks Updated",
            description=f"Channel: {channel.name}",
        )

        await self.send_to_audit_log(embed)

    """Audit Logging - Role"""

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """
        Logs when a role is created in a guild.

        Parameters
        ----------
        role : discord.Role
            The role that was created.
        """

        embed = EmbedCreator.create_log_embed(
            title="Role Created",
            description=f"Role: {role.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """
        Logs when a role is deleted in a guild.

        Parameters
        ----------
        role : discord.Role
            The role that was deleted.
        """

        embed = EmbedCreator.create_log_embed(
            title="Role Deleted",
            description=f"Role: {role.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        """
        Logs when a role is updated in a guild.

        Parameters
        ----------
        before : discord.Role
            The role before the update.
        after : discord.Role
            The role after the update.
        """

        embed = EmbedCreator.create_log_embed(
            title="Role Updated",
            description=f"Role: {before.name}",
        )

        await self.send_to_audit_log(embed)

    """Audit Logging - Scheduled Events"""

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent) -> None:
        """
        Logs when a scheduled event is created.

        Parameters
        ----------
        event : discord.ScheduledEvent
            The scheduled event that was created.
        """

        embed = EmbedCreator.create_log_embed(
            title="Scheduled Event Created",
            description=f"Event: {event.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent) -> None:
        """
        Logs when a scheduled event is deleted.

        Parameters
        ----------
        event : discord.ScheduledEvent
            The scheduled event that was deleted.
        """

        embed = EmbedCreator.create_log_embed(
            title="Scheduled Event Deleted",
            description=f"Event: {event.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_scheduled_event_update(
        self,
        before: discord.ScheduledEvent,
        after: discord.ScheduledEvent,
    ) -> None:
        """
        Logs when a scheduled event is updated.

        Parameters
        ----------
        before : discord.ScheduledEvent
            The scheduled event before the update.
        after : discord.ScheduledEvent
            The scheduled event after the update.
        """

        embed = EmbedCreator.create_log_embed(
            title="Scheduled Event Updated",
            description=f"Event: {before.name}",
        )

        await self.send_to_audit_log(embed)

    """Audit Logging - Stage Instance"""

    @commands.Cog.listener()
    async def on_stage_instance_create(self, stage_instance: discord.StageInstance) -> None:
        """
        Logs when a stage instance is created.

        Parameters
        ----------
        stage_instance : discord.StageInstance
            The stage instance that was created.
        """

        embed = EmbedCreator.create_log_embed(
            title="Stage Instance Created",
            description=f"Stage: {stage_instance.topic}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_stage_instance_delete(self, stage_instance: discord.StageInstance) -> None:
        """
        Logs when a stage instance is deleted.

        Parameters
        ----------
        stage_instance : discord.StageInstance
            The stage instance that was deleted.
        """

        embed = EmbedCreator.create_log_embed(
            title="Stage Instance Deleted",
            description=f"Stage: {stage_instance.topic}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_stage_instance_update(
        self,
        before: discord.StageInstance,
        after: discord.StageInstance,
    ) -> None:
        """
        Logs when a stage instance is updated.

        Parameters
        ----------
        before : discord.StageInstance
            The stage instance before the update.
        after : discord.StageInstance
            The stage instance after the update.
        """

        embed = EmbedCreator.create_log_embed(
            title="Stage Instance Updated",
            description=f"Stage: {before.topic}",
        )

        await self.send_to_audit_log(embed)

    """Audit Logging - Thread"""

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """
        Logs when a thread is created.

        Parameters
        ----------
        thread : discord.Thread
            The thread that was created.
        """

        embed = EmbedCreator.create_log_embed(
            title="Thread Created",
            description=f"Thread: {thread.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread) -> None:
        """
        Logs when a thread is deleted.

        Parameters
        ----------

        thread : discord.Thread
            The thread that was deleted.
        """

        embed = EmbedCreator.create_log_embed(
            title="Thread Deleted",
            description=f"Thread: {thread.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread) -> None:
        """
        Logs when a thread is updated.

        Parameters
        ----------
        before : discord.Thread
            The thread before the update.
        after : discord.Thread
            The thread after the update.
        """

        embed = EmbedCreator.create_log_embed(
            title="Thread Updated",
            description=f"Thread: {before.name}",
        )

        await self.send_to_audit_log(embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AuditLogging(bot))
