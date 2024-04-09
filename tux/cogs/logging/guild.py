from typing import Any

import discord
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator
from tux.utils.functions import compare_changes, extract_guild_attrs


class GuildLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.audit_log_channel_id: int = CONST.LOG_CHANNELS["AUDIT"]

    async def send_to_audit_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(self.audit_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    """Audit logging - Channel"""

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        embed = EmbedCreator.create_log_embed(
            title="Channel Created",
            description=f"Channel: {channel.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        embed = EmbedCreator.create_log_embed(
            title="Channel Deleted",
            description=f"Channel: {channel.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ):
        embed = EmbedCreator.create_log_embed(
            title="Channel Updated",
            description=f"Channel: {before.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(
        self,
        channel: discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel,
        last_pin: discord.Message | None,
    ):
        if isinstance(channel, discord.abc.GuildChannel | discord.Thread):
            channel_name = channel.name
        else:
            channel_name = "Private Channel"

        embed = EmbedCreator.create_log_embed(
            title="Channel Pins Updated", description=f"Channel: {channel_name}"
        )

        if isinstance(channel, discord.TextChannel | discord.Thread):
            pins = await channel.pins()
            if pins:
                embed.add_field(name="Latest pin", value=f"[Jump to message]({pins[0].jump_url})")

        await self.send_to_audit_log(embed)

    """Audit logging - Guild"""

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        before_attrs: dict[str, Any] = extract_guild_attrs(before)
        after_attrs: dict[str, Any] = extract_guild_attrs(after)

        embed = EmbedCreator.create_log_embed(title="Guild Updated", description="Before and after")

        if changes := compare_changes(before_attrs, after_attrs):
            embed.add_field(name="Changes", value="\n".join(changes).upper(), inline=False)

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(
        self, guild: discord.Guild, before: list[discord.Emoji], after: list[discord.Emoji]
    ):
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
            embed.add_field(
                name="Deleted Emoji",
                value=emojis_str[:1024],
            )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(
        self, guild: discord.Guild, before: list[discord.Sticker], after: list[discord.Sticker]
    ):
        embed = discord.Embed(
            title="Guild Stickers Updated",
            description=f"Stickers: {len(before)} -> {len(after)}",
        )

        new_stickers = [sticker for sticker in after if sticker not in before]
        deleted_stickers = [sticker for sticker in before if sticker not in after]

        if new_stickers:
            stickers_str = "\n".join(
                [f"[{sticker.name}]({sticker.url})" for sticker in new_stickers]
            )
            embed.add_field(name="Added Stickers", value=stickers_str[:1024])

            embed.set_image(url=new_stickers[0].url)

        if deleted_stickers:
            stickers_str = ", ".join([sticker.name for sticker in deleted_stickers])
            embed.add_field(name="Deleted Stickers", value=stickers_str[:1024])

        await self.send_to_audit_log(embed)

    """Audit logging - Integration"""

    @commands.Cog.listener()
    async def on_integration_create(self, integration: discord.Integration):
        embed = EmbedCreator.create_log_embed(
            title="Integration Created",
            description=f"Integration: {integration.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_integration_update(self, integration: discord.Integration):
        embed = EmbedCreator.create_log_embed(
            title="Integration Updated",
            description=f"Integration: {integration.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_integration_delete(self, integration: discord.Integration):
        embed = EmbedCreator.create_log_embed(
            title="Integration Deleted",
            description=f"Integration: {integration.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel):
        embed = EmbedCreator.create_log_embed(
            title="Webhooks Updated",
            description=f"Channel: {channel.name}",
        )

        await self.send_to_audit_log(embed)

    """Audit logging - Role"""

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        embed = EmbedCreator.create_log_embed(
            title="Role Created",
            description=f"Role: {role.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        embed = EmbedCreator.create_log_embed(
            title="Role Deleted",
            description=f"Role: {role.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        embed = EmbedCreator.create_log_embed(
            title="Role Updated",
            description=f"Role: {before.name}",
        )

        await self.send_to_audit_log(embed)

    """ Guild Logging - Scheduled Events"""

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        embed = EmbedCreator.create_log_embed(
            title="Scheduled Event Created",
            description=f"Event: {event.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        embed = EmbedCreator.create_log_embed(
            title="Scheduled Event Deleted",
            description=f"Event: {event.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_scheduled_event_update(
        self, before: discord.ScheduledEvent, after: discord.ScheduledEvent
    ):
        embed = EmbedCreator.create_log_embed(
            title="Scheduled Event Updated",
            description=f"Event: {before.name}",
        )

        await self.send_to_audit_log(embed)

    """Guild Logging - Stage Instance"""

    @commands.Cog.listener()
    async def on_stage_instance_create(self, stage_instance: discord.StageInstance):
        embed = EmbedCreator.create_log_embed(
            title="Stage Instance Created",
            description=f"Stage: {stage_instance.topic}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_stage_instance_delete(self, stage_instance: discord.StageInstance):
        embed = EmbedCreator.create_log_embed(
            title="Stage Instance Deleted",
            description=f"Stage: {stage_instance.topic}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_stage_instance_update(
        self, before: discord.StageInstance, after: discord.StageInstance
    ):
        embed = EmbedCreator.create_log_embed(
            title="Stage Instance Updated",
            description=f"Stage: {before.topic}",
        )

        await self.send_to_audit_log(embed)

    """Guild Logging - Thread"""

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        embed = EmbedCreator.create_log_embed(
            title="Thread Created",
            description=f"Thread: {thread.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        embed = EmbedCreator.create_log_embed(
            title="Thread Deleted",
            description=f"Thread: {thread.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        embed = EmbedCreator.create_log_embed(
            title="Thread Updated",
            description=f"Thread: {before.name}",
        )

        await self.send_to_audit_log(embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GuildLogging(bot))
