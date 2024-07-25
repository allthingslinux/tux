import discord
from discord.ext import commands

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class MemberLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.audit_log_channel_id: int = CONST.LOG_CHANNELS["AUDIT"]

    async def send_to_audit_log(self, embed: discord.Embed):
        channel = self.bot.get_channel(self.audit_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
        When a member is updated

        Parameters
        ----------
        before : discord.Member
            The member before the update.
        after : discord.Member
            The member after the update.
        """

        embed = EmbedCreator.create_log_embed(
            title="Member Updated",
            description=f"Member {before.mention} has been updated.",
        )

        if before.name != after.name:
            embed.add_field(name="Name", value=f"`{before.name}` -> `{after.name}`")

        if before.display_name != after.display_name:
            embed.add_field(
                name="Display Name",
                value=f"`{before.display_name}` -> `{after.display_name}`",
            )

        if before.global_name != after.global_name:
            embed.add_field(
                name="Global Name",
                value=f"`{before.global_name}` -> `{after.global_name}`",
            )

        await self.send_to_audit_log(embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberLogging(bot))
