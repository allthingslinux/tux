import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.models import Infractions
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator
from tux.utils.enums import InfractionType


class Ban(commands.Cog):
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

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod")
    @app_commands.command(name="ban", description="Bans a member from the server.")
    @app_commands.describe(member="Which member to ban", reason="Reason for ban")
    async def ban(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        """
        Bans a member from the server.

        Args:
            interaction: The interaction context for this command.
            member: The Discord member to be banned.
            reason: The reason for banning the member.
        """
        reason = reason or "No reason provided"

        try:
            new_ban = await self.insert_infraction(
                user_id=member.id,
                moderator_id=interaction.user.id,
                infraction_type=InfractionType.BAN,
                infraction_reason=reason,
            )

            embed = EmbedCreator.create_infraction_embed(
                title="",
                interaction=interaction,
                description="",
            )
            embed.add_field(
                name="Case ID", value=f"`{new_ban.id if new_ban else 'Unknown'}`", inline=True
            )
            embed.add_field(name="Action", value="Ban", inline=True)
            embed.add_field(name="Reason", value=f"`{reason}`", inline=False)
            embed.add_field(name="By", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="To", value=f"{member.mention}", inline=True)

            logger.info(f"Banned {member.display_name} ({member.id}): {reason}")

        except Exception as error:
            msg = f"Failed to ban {member.display_name} ({member.id})."
            embed = EmbedCreator.create_error_embed(
                title="Ban Failed", description=msg, interaction=interaction
            )

            logger.error(f"{msg} Error: {error}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
