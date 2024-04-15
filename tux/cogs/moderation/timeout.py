# import datetime

# import discord
# from discord import app_commands
# from discord.ext import commands
# from loguru import logger
# from tux.utils.enums import InfractionType
# from tux.utils.embeds import EmbedCreator


# class TimeOut(commands.Cog):
#     def __init__(self, bot: commands.Bot) -> None:
#         self.bot = bot

#     @app_commands.command(name="timeout", description="Timeout a user")

#     async def timeout(
#         self,
#         interaction: discord.Interaction,
#         member: discord.Member,

#         reason: str | None = None,
#     ) -> None:
#         logger.info(
#             f"{interaction.user} used the timeout command to timeout {member}",
#         )
#         try:
#             embed = discord.Embed(
#                 color=discord.Color.red(),
#                 title=f"User {member.display_name} timed out",
#                 description=f"Reason: {reason if reason else '`None provided`'}",
#                 timestamp=interaction.created_at,
#             )
#             embed.add_field(
#                 name="User",
#                 value=f"<@{member.id}>",
#                 inline=True,
#             )
#             embed.add_field(
#                 name="Duration",
#                 value=duration,
#                 inline=True,
#             )
#             embed.set_footer(
#                 text=f"Requested by {interaction.user.display_name}",
#                 icon_url=interaction.user.display_avatar,
#             )
#             await interaction.response.send_message(embed=embed)
#         except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
#             logger.error("")
#             embed_error = discord.Embed(
#                 colour=discord.Colour.red(),
#                 title=f"Failed to timeout {member.display_name}",
#                 description=f"`Error info: {e}`",
#                 timestamp=interaction.created_at,
#             )
#             embed_error.set_footer(
#                 text=f"Requested by {interaction.user.display_name}",
#                 icon_url=interaction.user.display_avatar,
#             )
#             await interaction.response.send_message(embed=embed_error)
#             return

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
        self.db_controller = DatabaseController().infractions

    async def insert_infraction(
        self,
        user_id: int,
        moderator_id: int,
        infraction_type: InfractionType,
        infraction_reason: str,
        expires_at: datetime.datetime | None = None,
    ) -> Infractions | None:
        """
        Inserts an infraction into the database.

        Args:
            user_id: The user ID who is being infracted.
            moderator_id: The moderator ID who is creating the infraction.
            infraction_type: The type of infraction.
            infraction_reason: The reason for the infraction.

        Returns:
            An instance of Infractions if successful, None otherwise.
        """
        try:
            return await self.db_controller.create_infraction(
                user_id=user_id,
                moderator_id=moderator_id,
                infraction_type=infraction_type,
                infraction_reason=infraction_reason,
                expires_at=expires_at,
            )

        except Exception as error:
            logger.error(f"Failed to create infraction for user {user_id}. Error: {error}")
            return None

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod")
    @app_commands.command(name="timeout", description="Timeout a member from the server.")
    @app_commands.describe(
        member="Which member to timeout",
        days="Days of timeout",
        hours="Hours of timeout",
        minutes="Minutes of timeout",
        seconds="Seconds of timeout",
        reason="Reason to timeout member",
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        reason: str | None = None,
    ) -> None:
        """
        Timeout a member from the server.

        Args:
            interaction: The interaction context for this command.
            member: The Discord member to timeout.
            reason: The reason for the member's timeout.
        """
        reason = reason or "No reason provided"

        duration = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

        try:
            await member.timeout(duration, reason=reason)

            new_timeout = await self.insert_infraction(
                user_id=member.id,
                moderator_id=interaction.user.id,
                infraction_type=InfractionType.TIMEOUT,
                infraction_reason=reason,
                expires_at=datetime.datetime.now(UTC) + duration,
            )

            embed = EmbedCreator.create_infraction_embed(
                title="",
                interaction=interaction,
                description="",
            )

            embed.add_field(
                name="Case ID",
                value=f"`{new_timeout.id if new_timeout else 'Unknown'}`",
                inline=True,
            )
            embed.add_field(name="Action", value="Timeout", inline=True)
            embed.add_field(name="Reason", value=f"`{reason}`", inline=False)
            embed.add_field(name="By", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="To", value=f"{member.mention}", inline=True)

            logger.info(f"Timed out {member.display_name} ({member.id}): {reason}")

        except Exception as error:
            msg = f"Failed to timeout {member.display_name} ({member.id})."
            embed = EmbedCreator.create_error_embed(
                title="Timeout Failed", description=msg, interaction=interaction
            )

            logger.error(f"{msg} Error: {error}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Timeout(bot))
