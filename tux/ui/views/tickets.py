from contextlib import suppress

import discord
from loguru import logger

from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks


class RequestCloseView(discord.ui.View):
    def __init__(self, cog, interaction: discord.Interaction, ticket, author):
        super().__init__(timeout=300)
        self.cog = cog
        self.original_interaction = interaction
        self.ticket = ticket
        self.author = author
        self.message = None

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ticket.author_id:
            await interaction.response.send_message("Only the ticket author can confirm close.", ephemeral=True)
            return

        try:
            # Respond to the button interaction first
            await interaction.response.send_message("Closing ticket...", ephemeral=True)

            # Create a mock context object for close_ticket method
            class MockContext:
                def __init__(self, guild, channel, user):
                    self.guild = guild
                    self.channel = channel
                    self.user = user
                    self.author = user

            mock_ctx = MockContext(interaction.guild, interaction.channel, interaction.user)

            # Call close_ticket without respond_to_interaction parameter
            await self.cog.close_ticket(mock_ctx, self.ticket, interaction.channel, self.author)

            # Clean up the confirmation message
            if self.message:
                with suppress(Exception):
                    await self.message.delete()

        except Exception as e:
            logger.error(f"Error in confirm_close: {e}")
            # Try to send an error message if the interaction hasn't been responded to
            with suppress(Exception):
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "An error occurred while closing the ticket.",
                        ephemeral=True,
                    )
                else:
                    await interaction.followup.send("An error occurred while closing the ticket.", ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            with suppress(Exception):
                await self.message.edit(content="Request to close ticket has timed out.", view=self)


class TicketManagementView(discord.ui.View):
    """View for managing tickets: only claim button is visible, all other management is via hidden slash commands."""

    def __init__(self, bot: Tux, ticket_id: int | None = None) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_id = ticket_id
        self.db = DatabaseController()

    async def update_view_for_ticket_state(self, interaction: discord.Interaction, ticket):
        """Update the view buttons based on the current ticket state."""
        claim_button = discord.utils.get(self.children, custom_id="ticket_claim")
        unclaim_button = discord.utils.get(self.children, custom_id="ticket_unclaim")

        if ticket.claimed_by:
            claimed_user = interaction.guild.get_member(ticket.claimed_by)
            claimed_name = claimed_user.display_name if claimed_user else "Unknown User"

            claim_button.label = f"Claimed by {claimed_name}"
            claim_button.disabled = True
            claim_button.style = discord.ButtonStyle.secondary

            if unclaim_button:
                unclaim_button.disabled = False
                unclaim_button.style = discord.ButtonStyle.danger
        else:
            claim_button.label = "Claim Ticket"
            claim_button.disabled = False
            claim_button.style = discord.ButtonStyle.primary

            if unclaim_button:
                unclaim_button.disabled = True
                unclaim_button.style = discord.ButtonStyle.secondary

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="ticket_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Claim a ticket for moderation."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        try:
            if not await checks.has_permission(interaction, 2, 9):
                await interaction.response.send_message(
                    "You need to be a moderator or higher to claim tickets.",
                    ephemeral=True,
                )
                return
        except Exception:
            await interaction.response.send_message(
                "You need to be a moderator or higher to claim tickets.",
                ephemeral=True,
            )
            return

        ticket = await self.db.ticket.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            await interaction.response.send_message("This channel is not a valid ticket.", ephemeral=True)
            return

        if ticket.claimed_by:
            claimed_user = interaction.guild.get_member(ticket.claimed_by)
            claimed_name = claimed_user.display_name if claimed_user else f"<@{ticket.claimed_by}>"
            await interaction.response.send_message(
                f"This ticket is already claimed by {claimed_name}.",
                ephemeral=True,
            )
            return

        updated_ticket = await self.db.ticket.claim_ticket(interaction.channel.id, interaction.user.id)
        if not updated_ticket:
            await interaction.response.send_message("Failed to claim the ticket.", ephemeral=True)
            return

        channel = interaction.channel
        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(
                interaction.guild.default_role,
                view_channel=False,
                reason="Ticket claimed - restricting access",
            )

            if author := interaction.guild.get_member(ticket.author_id):
                await channel.set_permissions(
                    author,
                    view_channel=True,
                    send_messages=True,
                    read_messages=True,
                    reason="Ticket author access",
                )

            await channel.set_permissions(
                interaction.user,
                view_channel=True,
                send_messages=True,
                read_messages=True,
                manage_messages=True,
                reason="Claiming moderator access",
            )
        # Update the view to reflect the claimed state
        await self.update_view_for_ticket_state(interaction, updated_ticket)

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.INFO,
            user_name=interaction.user.display_name,
            user_display_avatar=interaction.user.display_avatar.url,
            title="Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}.\n"
            f"Only the ticket author and claiming moderator can now access this channel.",
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Unclaim Ticket",
        style=discord.ButtonStyle.secondary,
        emoji="🔓",
        custom_id="ticket_unclaim",
        disabled=True,
    )
    async def unclaim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Unclaim a ticket, making it available for other moderators."""
        # Validate basic permissions and context
        validation_error = await self._validate_unclaim_context(interaction)
        if validation_error:
            await interaction.response.send_message(validation_error, ephemeral=True)
            return

        # Validate ticket state and unclaim permissions
        ticket = await self.db.ticket.get_ticket_by_channel(interaction.channel.id)
        permission_error = await self._validate_unclaim_permissions(interaction, ticket)
        if permission_error:
            await interaction.response.send_message(permission_error, ephemeral=True)
            return

        # Perform unclaim operation
        success = await self._perform_unclaim_operation(interaction, ticket)
        if not success:
            return

    async def _validate_unclaim_context(self, interaction: discord.Interaction) -> str | None:
        """Validate basic context for unclaim operation."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return "This command can only be used in a server."

        try:
            has_permission = await checks.has_permission(interaction, 2, 9)
        except Exception:
            has_permission = False

        if not has_permission:
            return "You need to be a moderator or higher to unclaim tickets."

        return None

    async def _validate_unclaim_permissions(self, interaction: discord.Interaction, ticket) -> str | None:
        """Validate ticket-specific unclaim permissions."""
        if not ticket:
            return "This channel is not a valid ticket."
        if not ticket.claimed_by:
            return "This ticket is not currently claimed."

        # Check if user can unclaim this specific ticket
        can_unclaim = ticket.claimed_by == interaction.user.id
        if not can_unclaim:
            try:
                can_unclaim = await checks.has_permission(interaction, 3, 9)
            except Exception:
                can_unclaim = False

        if not can_unclaim:
            claimed_user = interaction.guild.get_member(ticket.claimed_by)
            claimed_name = claimed_user.display_name if claimed_user else f"<@{ticket.claimed_by}>"
            return (
                "You can only unclaim tickets you have claimed yourself, or you need higher permissions. "
                f"This ticket is claimed by {claimed_name}."
            )

        return None

    async def _perform_unclaim_operation(self, interaction: discord.Interaction, ticket) -> bool:
        """Perform the actual unclaim operation."""
        updated_ticket = await self.db.ticket.unclaim_ticket(interaction.channel.id)
        if not updated_ticket:
            await interaction.response.send_message("Failed to unclaim the ticket.", ephemeral=True)
            return False

        # Restore channel permissions
        await self._restore_staff_permissions(interaction, ticket)

        # Update view and send response
        await self.update_view_for_ticket_state(interaction, updated_ticket)
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.INFO,
            user_name=interaction.user.display_name,
            user_display_avatar=interaction.user.display_avatar.url,
            title="Ticket Unclaimed",
            description=(
                f"This ticket has been unclaimed by {interaction.user.mention}.\n"
                "The ticket is now available for other staff members to claim."
            ),
        )
        await interaction.response.edit_message(embed=embed, view=self)
        return True

    async def _restore_staff_permissions(self, interaction: discord.Interaction, ticket):
        """Restore staff access to the unclaimed ticket."""
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return

        guild_config = await checks.fetch_guild_config(interaction.guild.id)
        staff_role_ids = {guild_config.get(f"perm_level_{lvl}_role_id") for lvl in range(2, 8)} - {None}

        for role in (r for r in interaction.guild.roles if r.id in staff_role_ids):
            await channel.set_permissions(
                role,
                view_channel=True,
                send_messages=True,
                read_messages=True,
                manage_messages=True,
                reason="Ticket unclaimed - restoring staff access",
            )

        if author := interaction.guild.get_member(ticket.author_id):
            await channel.set_permissions(author, view_channel=True, send_messages=True, read_messages=True)
