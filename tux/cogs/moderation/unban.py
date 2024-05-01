import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.models import Infractions
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator
from tux.utils.enums import InfractionType


class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_controller = DatabaseController()

    async def insert_infraction(
        self,
        user_id: int,
        moderator_id: int,
        infraction_type: InfractionType,
        infraction_reason: str,
    ) -> Infractions | None:
        """
        Inserts an infraction into the database.

        Parameters
        ----------
        user_id : int
            The ID of the user to issue the infraction to.
        moderator_id : int
            The ID of the moderator issuing the infraction.
        infraction_type : InfractionType
            The type of infraction to issue.
        infraction_reason : str
            The reason for issuing the infraction.

        Returns
        -------
        Infractions | None
            The infraction that was created, or None if an error occurred.
        """

        return await self.db_controller.infractions.create_infraction(
            user_id=user_id,
            moderator_id=moderator_id,
            infraction_type=infraction_type,
            infraction_reason=infraction_reason,
        )

    async def get_or_create_user(self, member: discord.User) -> None:
        """
        Retrieves a user from the database or creates a new user if not found.

        Parameters
        ----------
        member : discord.User
            The user to retrieve or create in the database.
        """

        user = await self.db_controller.users.get_user_by_id(member.id)

        if not user:
            await self.db_controller.users.create_user(
                user_id=member.id,
                name=member.name,
                display_name=member.display_name,
                mention=member.mention,
                bot=member.bot,
                created_at=member.created_at,
                joined_at=None,
            )

    async def get_or_create_moderator(self, interaction: discord.Interaction) -> None:
        """
        Retrieves a moderator from the database or creates a new moderator if not found.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """

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

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @app_commands.command(name="unban", description="Unbans a member from the server.")
    @app_commands.describe(
        username_or_id="The username of the member to unban", reason="Reason for unban"
    )
    async def unban(
        self, interaction: discord.Interaction, username_or_id: str, reason: str | None = None
    ) -> None:
        """
        Unbans a member from the server.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        username_or_id : str
            The username or ID of the member to unban.
        reason : str | None, optional
            The reason for unbanning the member, by default None

        Raises:
        -------
        ValueError
            If the user is not found in the ban list.
        """

        if interaction.guild is None:
            return

        # Get the list of banned users in the guild
        banned_users = [ban.user async for ban in interaction.guild.bans()]

        try:
            # If the username_or_id is an integer, search for the user by ID
            user_id = int(username_or_id)
            user_to_unban = discord.utils.get(banned_users, id=user_id)

        except ValueError:
            # If the username_or_id is not an integer, search for the user by username
            user_to_unban = discord.utils.find(lambda u: u.name == username_or_id, banned_users)

        if user_to_unban is None:
            await interaction.response.send_message(
                "User not found in the ban list. Please provide a valid user ID or username."
            )
            return

        try:
            await interaction.guild.unban(user_to_unban, reason=reason)

            await self.get_or_create_user(user_to_unban)
            await self.get_or_create_moderator(interaction)

            new_unban = await self.insert_infraction(
                user_id=user_to_unban.id,
                moderator_id=interaction.user.id,
                infraction_type=InfractionType.UNBAN,
                infraction_reason=reason or "No reason provided",
            )

            unban_id = new_unban.id if new_unban else "Unknown"

            embed = EmbedCreator.create_success_embed(
                title="Unban",
                description=f"Successfully unbanned {user_to_unban.display_name}.",
                interaction=interaction,
            )

            embed.add_field(name="Action", value="Unban", inline=False)
            embed.add_field(name="Case ID", value=unban_id, inline=False)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.add_field(name="User", value=user_to_unban.mention, inline=False)

            await interaction.response.send_message(embed=embed)

            logger.info(f"User {user_to_unban.display_name} has been unbanned.")

        except Exception as error:
            msg = f"Failed to unban user {user_to_unban.display_name}."

            embed = EmbedCreator.create_error_embed(
                title="Unban",
                description=msg,
                interaction=interaction,
            )

            logger.error(f"{msg} Error: {error}")

            await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unban(bot))
