import datetime

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger
from pytz import UTC

from prisma.models import Infractions
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator
from tux.utils.enums import InfractionType


class Timeout(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_controller = DatabaseController()

    async def insert_infraction(
        self,
        user_id: int,
        moderator_id: int,
        infraction_type: InfractionType,
        infraction_reason: str,
        expires_at: datetime.datetime | None = None,
    ) -> Infractions | None:
        try:
            return await self.db_controller.infractions.create_infraction(
                user_id=user_id,
                moderator_id=moderator_id,
                infraction_type=infraction_type,
                infraction_reason=infraction_reason,
                expires_at=expires_at,
            )

        except Exception as error:
            logger.error(f"Failed to create infraction for user {user_id}. Error: {error}")
            return None

    async def get_or_create_user(self, member: discord.Member) -> None:
        user = await self.db_controller.users.get_user_by_id(member.id)

        if not user:
            await self.db_controller.users.create_user(
                user_id=member.id,
                name=member.name,
                display_name=member.display_name,
                mention=member.mention,
                bot=member.bot,
                created_at=member.created_at,
                joined_at=member.joined_at,
            )

    async def get_or_create_moderator(self, interaction: discord.Interaction) -> None:
        moderator = await self.db_controller.users.get_user_by_id(interaction.user.id)
        moderator_context = None
        if interaction.guild:
            moderator_context = interaction.guild.get_member(interaction.user.id)

        if not moderator:
            await self.db_controller.users.create_user(
                user_id=interaction.user.id,
                name=interaction.user.name,
                display_name=interaction.user.display_name,
                mention=interaction.user.mention,
                bot=interaction.user.bot,
                created_at=interaction.user.created_at,
                joined_at=moderator_context.joined_at if moderator_context else None,
            )

    @app_commands.checks.has_any_role("Root", "Admin", "Sr. Mod", "Mod")
    @app_commands.command(name="timeout", description="Issues a timeout to a member of the server.")
    @app_commands.describe(
        member="The member to timeout",
        reason="The reason for issuing the timeout",
        days="Number of days for the timeout",
        hours="Number of hours for the timeout",
        minutes="Number of minutes for the timeout",
        seconds="Number of seconds for the timeout",
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = None,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> None:
        reason = reason or "No reason provided"

        duration = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

        await self.get_or_create_user(member)
        await self.get_or_create_moderator(interaction)

        try:
            await member.timeout(duration, reason=reason)

            new_timeout = await self.insert_infraction(
                user_id=member.id,
                moderator_id=interaction.user.id,
                infraction_type=InfractionType.TIMEOUT,
                infraction_reason=reason,
                expires_at=datetime.datetime.now(UTC) + duration,
            )

            timeout_id = new_timeout.id if new_timeout else "Unknown"

            embed = EmbedCreator.create_infraction_embed(
                title="",
                description="",
                interaction=interaction,
            )
            embed.add_field(name="Action", value="Timeout", inline=True)
            embed.add_field(name="Case ID", value=f"`{timeout_id}`", inline=True)
            embed.add_field(name="Reason", value=f"`{reason}`", inline=False)
            embed.add_field(name="Moderator", value=f"{interaction.user.display_name}", inline=True)
            embed.add_field(name="Member", value=f"{member.display_name}", inline=True)

            logger.info(f"Timeout issued to {member.display_name} ({member.id}) for: {reason}")

        except Exception as error:
            msg = f"Failed to issue timeout to {member.display_name}."
            embed = EmbedCreator.create_error_embed(
                title="Timeout Failed",
                description=msg,
                interaction=interaction,
            )

            logger.error(f"{msg} Error: {error}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Timeout(bot))
