import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.models import Infractions
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator
from tux.utils.enums import InfractionType


class Warn(commands.Cog):
    """Cog for handling the warning of members in a Discord server."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initializes the Warn Cog with the bot instance and a database controller reference."""
        self.bot = bot
        self.db_controller = DatabaseController().infractions

    async def insert_infraction(
        self,
        user_id: int,
        moderator_id: int,
        infraction_type: InfractionType,
        infraction_reason: str,
    ) -> Infractions | None:
        """
        Inserts a new warning infraction into the database.

        Args:
            user_id: ID of the user receiving the infraction.
            moderator_id: ID of the moderator issuing the infraction.
            infraction_type: Type of infraction, e.g., WARN.
            infraction_reason: Reason for issuing the infraction.

        Returns:
            An Infractions object if creation was successful, None otherwise.
        """
        try:
            return await self.db_controller.create_infraction(
                user_id=user_id,
                moderator_id=moderator_id,
                infraction_type=infraction_type,
                infraction_reason=infraction_reason,
            )

        except Exception as error:
            logger.error(f"Failed to create infraction for user {user_id}. Error: {error}")
            return None

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="warn", description="Issues a warning to a member of the server.")
    @app_commands.describe(member="The member to warn", reason="The reason for issuing the warning")
    async def warn(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        """
        Warns a specified member with an optional reason.

        Args:
            interaction: The Discord interaction context.
            member: The member object representing the user to warn.
            reason: The reason for warning the user.
        """
        reason = reason or "No reason provided"

        try:
            warn_entry = await self.insert_infraction(
                user_id=member.id,
                moderator_id=interaction.user.id,
                infraction_type=InfractionType.WARN,
                infraction_reason=reason,
            )

            warn_id = warn_entry.id if warn_entry else "Unknown"

            embed = EmbedCreator.create_infraction_embed(
                title="",
                description="",
                interaction=interaction,
            )
            embed.add_field(name="Action", value="Warn", inline=True)
            embed.add_field(name="Case ID", value=f"`{warn_id}`", inline=True)
            embed.add_field(name="Reason", value=f"`{reason}`", inline=False)
            embed.add_field(name="Moderator", value=f"{interaction.user.display_name}", inline=True)

            logger.info(f"Warning issued to {member.display_name} ({member.id}) for: {reason}")

        except Exception as error:
            msg = f"Failed to issue warning to {member.display_name}."
            embed = EmbedCreator.create_error_embed(
                title="Warning Failed",
                description=msg,
                interaction=interaction,
            )

            logger.error(f"{msg} Error: {error}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Asynchronously adds the Warn cog to the bot."""
    await bot.add_cog(Warn(bot))
