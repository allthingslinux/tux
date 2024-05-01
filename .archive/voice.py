from typing import Any

import discord
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class VoiceLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.audit_log_channel_id: int = CONST.LOG_CHANNELS["AUDIT"]
        self.mod_log_channel_id: int = CONST.LOG_CHANNELS["MOD"]

    async def send_to_audit_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(self.audit_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    def get_channel_change(self, before: discord.VoiceState, after: discord.VoiceState) -> str:
        if before.channel != after.channel:
            if after.channel:
                return f"has joined {after.channel.name}."
            if before.channel:
                return f"has left {before.channel.name}."
        return ""

    def get_state_change(self, state_name: str, before_state: Any, after_state: Any) -> str:
        if before_state != after_state:
            action = state_name + ("d" if after_state else "ed")
            return f"has been {action}."
        return ""

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        embed = EmbedCreator.create_log_embed(
            title="Voice State Update",
            description=f"User: {member.name}",
        )

        changes: list[str] = []

        if channel_change := self.get_channel_change(before, after):
            changes.append(channel_change)

        if mute_change := self.get_state_change("mute", before.self_mute, after.self_mute):
            changes.append(mute_change)

        if deaf_change := self.get_state_change("deaf", before.self_deaf, after.self_deaf):
            changes.append(deaf_change)

        if stream_change := self.get_state_change(
            "start streaming", before.self_stream, after.self_stream
        ):
            changes.append(stream_change)

        if video_change := self.get_state_change(
            "start video", before.self_video, after.self_video
        ):
            changes.append(video_change)

        if changes:
            embed.add_field(name="Changes", value=" ".join(changes), inline=False)

            await self.send_to_audit_log(embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceLogging(bot))
