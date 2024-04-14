import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

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
    ) -> None:
        try:
            await self.db_controller.create_infraction(
                user_id=user_id,
                moderator_id=moderator_id,
                infraction_type=infraction_type,
                infraction_reason=infraction_reason,
            )

        except Exception as error:
            logger.error(f"Failed to create infraction. Error: {error}")

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="ban", description="Bans a member from the server.")
    @app_commands.describe(member="Which member to ban", reason="Reason for ban")
    async def ban(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        try:
            await member.ban(reason=reason)

            embed = EmbedCreator.create_infraction_embed(
                title=f"{member.display_name} has been banned.",
                description=f"Reason: `{reason}`",
                interaction=interaction,
            )

            embed.add_field(
                name="Moderator",
                value=f"{interaction.user.mention} ({interaction.user.id})",
                inline=False,
            )

            embed.add_field(
                name="Member",
                value=f"{member.mention} ({member.id})",
                inline=False,
            )

            await self.insert_infraction(
                user_id=member.id,
                moderator_id=interaction.user.id,
                infraction_type=InfractionType.BAN,
                infraction_reason=reason or "None provided",
            )

            logger.info(f"Bannedd {member.display_name} for: {reason}")

        except Exception as error:
            embed = EmbedCreator.create_error_embed(
                title=f"Failed to ban {member.display_name}",
                description=f"Error Info: `{error}`",
                interaction=interaction,
            )

            logger.error(f"Failed to ban {member.display_name}. Error: {error}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ban(bot))
