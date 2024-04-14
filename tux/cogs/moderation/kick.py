import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator
from tux.utils.enums import InfractionType


class Kick(commands.Cog):
    """Cog for handling the kicking of members from a Discord server."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_controller = DatabaseController().infractions

    async def insert_infraction(
        self,
        user_id: int,
        moderator_id: int,
        infraction_type: InfractionType,
        infraction_reason: str,
    ) -> None:
        """Inserts an infraction record into the database."""
        try:
            await self.db_controller.create_infraction(
                user_id=user_id,
                moderator_id=moderator_id,
                infraction_type=infraction_type,
                infraction_reason=infraction_reason,
            )
            logger.info("Infraction recorded successfully.")
        except Exception as error:
            logger.error(f"Failed to create infraction. Error: {error}")

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="kick", description="Kicks a member from the server.")
    @app_commands.describe(member="Member to kick", reason="Reason for the kick")
    async def kick(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        """Kicks the specified member with an optional reason."""
        if reason is None:
            reason = "No reason provided"

        try:
            await member.kick(reason=reason)
            await self.log_kick(interaction, member, reason)
        except Exception as error:
            await self.handle_kick_error(interaction, member, error)

    async def log_kick(
        self, interaction: discord.Interaction, member: discord.Member, reason: str
    ) -> None:
        """Sends a log message and informs about the kick operation."""
        embed = EmbedCreator.create_infraction_embed(
            title=f"{member.display_name} has been kicked.",
            description=f"Reason: `{reason}`",
            interaction=interaction,
        )
        embed.add_field(
            name="Moderator",
            value=f"{interaction.user.mention} ({interaction.user.id})",
            inline=False,
        )
        embed.add_field(name="Member", value=f"{member.mention} ({member.id})", inline=False)

        await self.insert_infraction(
            user_id=member.id,
            moderator_id=interaction.user.id,
            infraction_type=InfractionType.KICK,
            infraction_reason=reason,
        )
        logger.info(f"Kicked {member.display_name} for: {reason}")
        await interaction.response.send_message(embed=embed)

    async def handle_kick_error(
        self, interaction: discord.Interaction, member: discord.Member, error: Exception
    ) -> None:
        """Handles errors that occur during the kick operation."""
        error_msg = f"Failed to kick {member.display_name}. Error: {error}"
        logger.error(error_msg)
        embed = EmbedCreator.create_error_embed(
            title=f"Failed to kick {member.display_name}",
            description=f"Error Info: `{error}`",
            interaction=interaction,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Kick(bot))
