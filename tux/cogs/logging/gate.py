import discord
from discord.ext import commands

from tux.database.controllers import DatabaseController
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator
from tux.utils.functions import datetime_to_elapsed_time, datetime_to_unix


class GateLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_controller = DatabaseController()
        self.gate_log_channel_id: int = CONST.LOG_CHANNELS["GATE"]
        self.dev_log_channel_id: int = CONST.LOG_CHANNELS["DEV"]

    async def send_to_gate_log(self, embed: discord.Embed) -> None:
        channel = self.bot.get_channel(self.gate_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    async def send_to_dev_log(self, embed: discord.Embed) -> None:
        channel = self.bot.get_channel(self.dev_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        When a member joins the server

        Parameters
        ----------
        member : discord.Member
            The member that joined the server.
        """

        gate_embed = EmbedCreator.create_log_embed(
            title="Member Joined", description=f"Welcome {member.mention}!"
        )

        created_at = datetime_to_unix(member.created_at)
        account_age = datetime_to_elapsed_time(member.created_at)

        gate_embed.add_field(name="User", value=member)
        gate_embed.add_field(name="ID", value=f"`{member.id}`")
        gate_embed.add_field(
            name="Account Age", value=f"{account_age} ago ({created_at})", inline=False
        )
        gate_embed.set_thumbnail(url=member.display_avatar)

        await self.send_to_gate_log(gate_embed)

        new_user = await self.db_controller.users.sync_user(
            user_id=member.id,
            name=member.name,
            display_name=member.display_name,
            mention=member.mention,
            bot=member.bot,
            created_at=member.created_at,
            joined_at=member.joined_at,
        )

        log_embed = EmbedCreator.create_log_embed(
            title="Database User Synced",
            description=f"User {member.mention} (`{new_user.id}`) synced to database."
            if new_user is not None
            else f"User {member.mention} synced to database.",
        )

        await self.send_to_dev_log(log_embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """
        When a member leaves the server

        Parameters
        ----------
        member : discord.Member
            The member that left the server.
        """

        embed = EmbedCreator.create_log_embed(
            title="Member Left",
            description=f"Goodbye {member.mention}!",
        )

        joined_at_ago = ""

        if member.joined_at is not None:
            joined_at = datetime_to_unix(member.joined_at)
            joined_at_ago = datetime_to_elapsed_time(member.joined_at)
        else:
            joined_at = "Unknown"

        embed.add_field(name="User", value=member)
        embed.add_field(name="ID", value=f"`{member.id}`")
        embed.add_field(name="Join Age", value=f"{joined_at_ago} ago ({joined_at})", inline=False)
        embed.set_thumbnail(url=member.display_avatar)

        await self.send_to_gate_log(embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite) -> None:
        """
        When an invite is created

        Parameters
        ----------
        invite : discord.Invite
            The invite that was created.
        """

        if invite.expires_at is not None:
            expires_at = datetime_to_unix(invite.expires_at)
        else:
            expires_at = "Never"

        max_uses = "Unlimited" if invite.max_uses == 0 else invite.max_uses

        embed = EmbedCreator.create_log_embed(
            title="Invite Created",
            description=f"New invite `{invite.code}` created by `{invite.inviter}`",
        )
        embed.add_field(name="Channel", value=invite.channel)
        embed.add_field(name="Max Uses", value=max_uses)
        embed.add_field(name="Expires At", value=expires_at)

        await self.send_to_gate_log(embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GateLogging(bot))
