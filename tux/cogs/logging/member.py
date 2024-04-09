from typing import Any

import discord
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator
from tux.utils.functions import compare_changes, extract_member_attrs


class MemberLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.audit_log_channel_id: int = CONST.LOG_CHANNELS["AUDIT"]
        self.mod_log_channel_id: int = CONST.LOG_CHANNELS["MOD"]

    async def send_to_audit_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(self.audit_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        embed = EmbedCreator.create_log_embed(
            title="Invite Created",
            description=f"Invite: {invite.url}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        embed = EmbedCreator.create_log_embed(
            title="Invite Deleted",
            description=f"Invite: {invite.url}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = EmbedCreator.create_log_embed(
            title="Member Joined",
            description=f"User: {member.name}",
        )

        await self.send_to_audit_log(embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Called when a Member leaves a Guild.

        If the guild or member could not be found in the internal cache, this event will not be called, you may use on_raw_member_remove() instead.

        Args:
            member: The discord.Member instance representing the member being removed.

        Returns:
            None
        """

        embed = EmbedCreator.create_log_embed(
            title="Member Removed",
            description=f"User: {member.name}",
        )

        await self.send_to_audit_log(embed)

    """Mod logging - Member"""

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        before_attrs: dict[str, Any] = extract_member_attrs(before)
        after_attrs: dict[str, Any] = extract_member_attrs(after)

        embed = EmbedCreator.create_log_embed(
            title="Member Updated", description="Before and after"
        )

        if changes := compare_changes(before_attrs, after_attrs):
            embed.add_field(name="Changes", value="\n".join(changes).upper(), inline=False)

        await self.send_to_audit_log(embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberLogging(bot))
