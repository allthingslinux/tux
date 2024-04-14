import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.models import Infractions
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator
from tux.utils.enums import InfractionType


class Warn(commands.Cog):
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
        try:
            return await self.db_controller.create_infraction(
                user_id=user_id,
                moderator_id=moderator_id,
                infraction_type=infraction_type,
                infraction_reason=infraction_reason,
            )
        except Exception as error:
            logger.error(f"Failed to create infraction. Error: {error}")

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="warn", description="Warns a member from the server.")
    @app_commands.describe(member="Which member to warn", reason="Reason for warn")
    async def warn(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        try:
            new_warn: Infractions | None = await self.insert_infraction(
                user_id=member.id,
                moderator_id=interaction.user.id,
                infraction_type=InfractionType.WARN,
                infraction_reason=reason or "None provided",
            )

            warn_id = new_warn.id if new_warn is not None else "Unknown"

            embed = EmbedCreator.create_infraction_embed(
                title=f"WARNING — ID: {warn_id}", interaction=interaction, description=""
            )

            embed.add_field(
                name="Reason",
                value=f"`{reason}`" if reason else "No reason provided",
                inline=False,
            )

            embed.add_field(
                name="By",
                value=f"{interaction.user.mention} `({interaction.user.id})`",
                inline=True,
            )

            embed.add_field(
                name="To",
                value=f"{member.mention} `({member.id})`",
                inline=True,
            )

            logger.info(f"Warned {member.display_name} for: {reason}")

        except Exception as error:
            embed = EmbedCreator.create_error_embed(
                title=f"Failed to warn {member.display_name}",
                description=f"Error Info: `{error}`",
                interaction=interaction,
            )

            logger.error(f"Failed to warn {member.display_name}. Error: {error}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warn(bot))
