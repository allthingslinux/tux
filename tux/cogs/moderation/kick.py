import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.models import Infractions
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator
from tux.utils.enums import InfractionType


class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
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
            )

        except Exception as error:
            logger.error(f"Failed to create infraction for user {user_id}. Error: {error}")
            return None

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="kick", description="Kicks a member from the server.")
    @app_commands.describe(member="Which member to kick", reason="Reason for kick")
    async def kick(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        """
        Kicks a member from the server.

        Args:
            interaction: The interaction context for this command.
            member: The Discord member to be kicked.
            reason: The reason for kicking the member.
        """
        reason = reason or "No reason provided"

        try:
            new_kick = await self.insert_infraction(
                user_id=member.id,
                moderator_id=interaction.user.id,
                infraction_type=InfractionType.KICK,
                infraction_reason=reason,
            )

            embed = EmbedCreator.create_infraction_embed(
                title="",
                interaction=interaction,
                description="",
            )
            embed.add_field(
                name="Case ID", value=f"`{new_kick.id if new_kick else 'Unknown'}`", inline=True
            )
            embed.add_field(name="Action", value="Kick", inline=True)
            embed.add_field(name="Reason", value=f"`{reason}`", inline=False)
            embed.add_field(name="By", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="To", value=f"{member.mention}", inline=True)

            logger.info(f"Kicked {member.display_name} ({member.id}): {reason}")

        except Exception as error:
            msg = f"Failed to kick {member.display_name} ({member.id})."
            embed = EmbedCreator.create_error_embed(
                title="Kick Failed", description=msg, interaction=interaction
            )

            logger.error(f"{msg} Error: {error}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Kick(bot))
