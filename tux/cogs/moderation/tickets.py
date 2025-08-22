import asyncio
import re
import traceback
from collections import defaultdict
from contextlib import suppress

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.enums import TicketStatus
from tux.bot import Tux
from tux.database.controllers import DatabaseController, guild_config
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.ui.views.tickets import RequestCloseView, TicketManagementView
from tux.utils import checks


class TicketCreationError(Exception):
    """Raised when a ticket cannot be created or initialized properly."""


class Tickets(commands.Cog):
    # Central small helpers to unify patterns
    @staticmethod
    def _ticket_error(message: str) -> TicketCreationError:
        return TicketCreationError(message)

    def _raise_creation_error(self, message: str) -> None:
        """Raise ticket creation error with proper message handling."""
        msg = message
        raise TicketCreationError(msg)

    def _raise_persist_error(self, message: str) -> None:
        """Raise ticket persistence error with proper message handling."""
        msg = message
        raise TicketCreationError(msg)

    async def show_transcript(self, interaction: discord.Interaction, ticket_id: int):
        """Show the transcript for a ticket as a .txt file, even if the channel is deleted."""
        await interaction.response.defer(ephemeral=True)
        ticket = await self.db.ticket.get_ticket_by_id(ticket_id)
        if not ticket or ticket.guild_id != interaction.guild.id:
            await interaction.followup.send("Ticket not found.", ephemeral=True)
            return

        ticket_log_cog = self.bot.get_cog("TicketLog")
        if not ticket_log_cog:
            await interaction.followup.send("Transcript system not available.", ephemeral=True)
            return

        if channel := interaction.guild.get_channel(ticket.channel_id):
            try:
                messages = [msg async for msg in channel.history(limit=100, oldest_first=True)]
                success = await ticket_log_cog.log_transcript(interaction.guild, channel, ticket, messages)
                if success:
                    transcript_file = await ticket_log_cog.get_transcript_from_log(
                        interaction.guild.id,
                        ticket.channel_id,
                    )
                    if transcript_file:
                        await interaction.followup.send(
                            content="Here is the ticket transcript.",
                            file=transcript_file,
                            ephemeral=True,
                        )
                        return
                await interaction.followup.send("Failed to generate transcript.", ephemeral=True)
            except Exception as e:
                logger.error(f"Error creating live transcript: {e}")
                await interaction.followup.send("Error generating transcript.", ephemeral=True)
        else:
            transcript_file = await ticket_log_cog.get_transcript_from_log(
                interaction.guild.id,
                ticket.channel_id,
            )
            if transcript_file:
                await interaction.followup.send(
                    content="Here is the ticket transcript from logs.",
                    file=transcript_file,
                    ephemeral=True,
                )
                return
            await interaction.followup.send("Transcript not found.", ephemeral=True)

    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.guild_config_controller = guild_config.GuildConfigController()
        self.cleanup_tasks: dict[int, asyncio.Task] = {}  # Store cleanup tasks by channel_id

    async def close_ticket(self, ctx, ticket, channel, author, respond_to_interaction=None):
        """Close a ticket, log transcript, update permissions, and remove resources."""
        self._cancel_cleanup_task(channel.id)
        self._log_ticket_closed_event(ctx, channel.id)
        await self._mark_ticket_closed(ticket, channel.id)
        overwrites = await self._build_closure_overwrites(ctx, author, ticket)
        await channel.edit(overwrites=overwrites, reason="Ticket closed (restricted access)")
        await self._send_closure_embed(channel)
        await self._attempt_transcript_log(ctx, channel, ticket)
        await self._delete_channel_and_category(channel)

    def _log_ticket_closed_event(self, ctx, channel_id: int) -> None:
        ticket_log_cog = self.bot.get_cog("TicketLog")
        if not ticket_log_cog:
            return
        if closer_id := getattr(
            getattr(ctx, "author", None), "id", None
        ) or getattr(getattr(ctx, "user", None), "id", None):
            ticket_log_cog.add_ticket_event(
                channel_id,
                "TICKET_CLOSED",
                closer_id,
                "Ticket closed by staff member",
            )

    async def _mark_ticket_closed(self, ticket, channel_id: int) -> None:
        try:
            if hasattr(self.db.ticket, "close_ticket"):
                await self.db.ticket.close_ticket(channel_id)
            elif hasattr(self.db.ticket, "update_ticket"):
                await self.db.ticket.update_ticket(ticket.ticket_id, status=TicketStatus.CLOSED)
        except Exception as e:
            logger.error(f"Failed updating ticket status {ticket.ticket_id}: {e}")

    async def _build_closure_overwrites(self, ctx, author, ticket) -> dict:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_messages=True,
                manage_messages=True,
                manage_channels=True,
            ),
        }
        claimed_by = getattr(ticket, "claimed_by", None)
        if not claimed_by:
            return overwrites
        if claimed_member := ctx.guild.get_member(claimed_by):
            overwrites[claimed_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=False,
                read_messages=True,
            )
        # Fetch Jr. Mod / Mod roles (levels 2 & 3) for view-only access
        try:
            cfg = await checks.fetch_guild_config(ctx.guild.id)
            desired_ids = {cfg.get("perm_level_2_role_id"), cfg.get("perm_level_3_role_id")} - {None}
            for role in ctx.guild.roles:
                if role.id in desired_ids:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=False,
                        read_messages=True,
                    )
        except Exception as e:
            logger.warning(f"Failed building closure overwrites for ticket {ticket.ticket_id}: {e}")
        return overwrites

    async def _send_closure_embed(self, channel: discord.TextChannel) -> None:
        try:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedType.INFO,
                user_name="System",
                user_display_avatar=self.bot.user.display_avatar.url,
                title="Ticket Closed",
                description="This ticket has been closed. The channel will be deleted.",
            )
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed sending closure embed in {channel.id}: {e}")

    async def _attempt_transcript_log(self, ctx, channel: discord.TextChannel, ticket) -> None:
        ticket_log_cog = self.bot.get_cog("TicketLog")
        if not ticket_log_cog:
            return
        try:
            messages = [msg async for msg in channel.history(oldest_first=True)]
            success = await ticket_log_cog.log_transcript(ctx.guild, channel, ticket, messages)
            log_func = logger.info if success else logger.warning
            log_func(
                f"{'Successfully' if success else 'Failed to'} log transcript for ticket {ticket.ticket_id}",
            )
        except Exception as e:
            logger.error(f"Transcript logging error for ticket {ticket.ticket_id}: {e}")

    async def _delete_channel_and_category(self, channel: discord.TextChannel) -> None:
        category = getattr(channel, "category", None)
        with suppress(Exception):
            await channel.delete(reason="Ticket closed and auto-removed.")
        if not category or not isinstance(category, discord.CategoryChannel):
            return
        if len(category.channels) == 0:
            with suppress(Exception):
                await category.delete(reason="Temporary ticket category auto-removed.")

    async def _ephemeral_msg(self, ctx, content):
        # If content is an embed, send as embed
        if isinstance(content, discord.Embed):
            msg = await ctx.send(embed=content, ephemeral=True)
        else:
            msg = await ctx.send(content, ephemeral=True)
        await asyncio.sleep(10)
        with suppress(Exception):
            await msg.delete()

    def _resolve_target(self, ctx, target):
        """Resolve a user or role from a string or object.

        Returns discord.Member | discord.Role | None
        """
        if isinstance(target, discord.Member | discord.Role):  # UP038
            return target

        s = str(target).strip()
        guild = ctx.guild
        id_candidates: set[int] = set()
        if s.isdigit():
            id_candidates.add(int(s))
        for pattern in (r"<@!?([0-9]+)>", r"<@&([0-9]+)>"):
            match = re.fullmatch(pattern, s)
            if match:
                id_candidates.add(int(match.group(1)))

        for cid in id_candidates:
            member = guild.get_member(cid)
            if member:
                return member
            role = guild.get_role(cid)
            if role:
                return role

        lowered = s.lower()
        member = discord.utils.find(
            lambda m: m.name.lower() == lowered or m.display_name.lower() == lowered,
            guild.members,
        )
        if member:
            return member
        return discord.utils.find(lambda r: r.name.lower() == lowered, guild.roles)

    @app_commands.command(name="ticket_request_close", description="Request to close the ticket (staff only)")
    @app_commands.guild_only()
    @checks.ac_has_pl(2)
    async def ticket_request_close(self, interaction: discord.Interaction):
        """Slash command to request close (staff members)."""
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "This command can only be used in a ticket channel.",
                ephemeral=True,
            )
            return
        ticket = await self.db.ticket.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            await interaction.response.send_message("This is not a valid ticket channel.", ephemeral=True)
            return

        author = interaction.guild.get_member(ticket.author_id)
        if not author:
            await interaction.response.send_message("Ticket author not found.", ephemeral=True)
            return

        view = RequestCloseView(self, interaction, ticket, author)
        await interaction.channel.send(
            f"{author.mention}, a staff member has requested to close this ticket. Please confirm:",
            view=view,
        )
        await interaction.response.send_message("Confirmation sent to ticket author.", ephemeral=True)

    @commands.hybrid_group(name="ticket", aliases=["t"], invoke_without_command=True)
    async def ticket(self, ctx: commands.Context):
        """
        Ticket command group. Use subcommands to manage tickets.
        """
        help_msg = (
            "Use `$ticket create [title]` or `/ticket create [title]` to open a ticket. "
            "Use `$ticket list` to list tickets.\n"
            "See the wiki for more info."
        )
        if isinstance(ctx, commands.Context):
            await ctx.send(help_msg)
        else:
            await ctx.response.send_message(help_msg, ephemeral=True)

    @ticket.command(name="create")
    @app_commands.describe(title="The title/subject of your ticket (optional)")
    async def create(self, ctx: commands.Context, *, title: str | None = None):
        """Create a new support ticket (hybrid command)."""
        user, guild, send = self._extract_ctx(ctx)
        self._maybe_delete_invocation(ctx)
        if error := self._validate_creation_prereqs(guild, user, title):
            await send(error, ephemeral=True)
            return
        title = self._normalize_title(title)

        if hasattr(ctx, "response") and hasattr(ctx.response, "defer"):
            await ctx.response.defer(ephemeral=True)

        try:
            await self._ensure_guild_config(guild.id)
            if await self._user_has_open_ticket(guild.id, user.id):
                await send("You already have an open ticket. Please use that one or close it first.", ephemeral=True)
                return
            ticket = await self.db.ticket.create_ticket(
                guild_id=guild.id,
                channel_id=0,
                author_id=user.id,
                title=title,
            )
            if not ticket:
                self._raise_creation_error("Failed to create ticket database entry")

            overwrites = await self._build_initial_overwrites(guild, user)
            ticket_channel, category = await self._make_ticket_channel(guild, ticket, user, overwrites)
            await self._persist_channel_id(ticket, ticket_channel, category)
            await self._post_ticket_intro(ticket_channel, user, ticket, title)
            cleanup_task = asyncio.create_task(
                self._schedule_unclaimed_cleanup(
                    ticket_channel.id,
                    category.id if category else None,
                ),
            )
            self.cleanup_tasks[ticket_channel.id] = cleanup_task
            await self._ephemeral_success(send, ticket, ticket_channel)
        except TicketCreationError as e:
            logger.warning(f"Ticket creation aborted: {e}")
            await send(str(e), ephemeral=True)
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            await send("An error occurred while creating your ticket. Please try again later.", ephemeral=True)

    # ---- Creation helpers ----
    def _extract_ctx(self, ctx):
        if isinstance(ctx, commands.Context):
            return ctx.author, ctx.guild, ctx.send
        return ctx.user, ctx.guild, ctx.response.send_message

    def _maybe_delete_invocation(self, ctx):
        if isinstance(ctx, commands.Context):
            with suppress(discord.NotFound, discord.Forbidden):
                task = asyncio.create_task(ctx.message.delete())
                ctx._delete_invocation_task = task

    def _validate_creation_prereqs(self, guild, user, title):
        if not guild or not isinstance(user, discord.Member):
            return "This command can only be used in a server."
        if not title or not title.strip():
            return None
        if len(title) > 100:
            return "Ticket title must be 100 characters or less."
        if len(title.strip()) < 3:
            return "Ticket title must be at least 3 characters long."
        return None

    def _normalize_title(self, title):
        return "No subject provided" if not title or not title.strip() else title.strip()

    async def _ensure_guild_config(self, guild_id: int):
        if not await self.guild_config_controller.get_guild_config(guild_id):
            await self.guild_config_controller.insert_guild_config(guild_id)

    async def _user_has_open_ticket(self, guild_id: int, user_id: int) -> bool:
        existing = await self.db.ticket.get_user_tickets(guild_id, user_id, TicketStatus.OPEN)
        return bool(existing)

    async def _build_initial_overwrites(self, guild: discord.Guild, user: discord.Member):
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                manage_messages=True,
                manage_channels=True,
            ),
        }
        cfg = await checks.fetch_guild_config(guild.id)
        staff_role_ids = {
            cfg.get("perm_level_2_role_id"),
            cfg.get("perm_level_3_role_id"),
        } - {None}
        for role in guild.roles:
            if role.id in staff_role_ids:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_messages=True,
                    manage_messages=True,
                )
        return overwrites

    async def _make_ticket_channel(self, guild: discord.Guild, ticket, user, overwrites):
        channel_name = f"ticket-{ticket.ticket_id}"
        category = None
        try:
            category = await guild.create_category(name=channel_name, reason=f"Temporary category for {channel_name}")
            ticket_channel = await guild.create_text_channel(
                channel_name,
                overwrites=overwrites,
                category=category,
                reason=f"Ticket #{ticket.ticket_id} created by {user}",
            )
        except Exception as e:
            if category:
                with suppress(Exception):
                    await category.delete(reason="Cleanup after failed ticket channel creation")
            await self.db.ticket.delete_ticket(ticket.ticket_id)
            msg = "Failed to create ticket channel. Please try again later."
            raise TicketCreationError(msg) from e
        else:
            return ticket_channel, category

    async def _persist_channel_id(self, ticket, ticket_channel, category):
        try:
            updated = await self.db.ticket.update(
                where={"ticket_id": ticket.ticket_id},
                data={"channel_id": ticket_channel.id},
            )
            if not updated:
                self._raise_persist_error("Failed to update ticket with channel ID")
        except Exception as e:
            with suppress(Exception):
                await ticket_channel.delete(reason="Failed to update ticket in database")
            if category:
                with suppress(Exception):
                    await category.delete(reason="Cleanup after failed ticket DB update")
            await self.db.ticket.delete_ticket(ticket.ticket_id)
            if isinstance(e, TicketCreationError):
                raise
            emsg = "Failed to create ticket. Please try again later."
            raise TicketCreationError(emsg) from e

    async def _post_ticket_intro(self, channel: discord.TextChannel, user: discord.Member, ticket, title: str):
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.INFO,
            user_name=user.display_name,
            user_display_avatar=user.display_avatar.url,
            title=f"Ticket #{ticket.ticket_id}",
            description=(
                f"Hello {user.mention}! Thank you for creating a support ticket.\n\n"
                f"**Reason:** {title}\n\n"
                f"**Please describe your issue in detail below.**\n\nA staff member will be with you shortly."
            ),
        )
        embed.add_field(name="Ticket ID", value=f"#{ticket.ticket_id}", inline=True)
        embed.add_field(name="Status", value="Open", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(ticket.created_at.timestamp())}:R>", inline=True)
        view = TicketManagementView(self.bot, ticket.ticket_id)
        await channel.send(content=f"{user.mention}", embed=embed, view=view)

    async def _schedule_unclaimed_cleanup(self, channel_id: int, category_id: int | None, delay_seconds: int = 14400):
        try:
            await asyncio.sleep(delay_seconds)
            ticket = await self.db.ticket.get_ticket_by_channel(channel_id)
            if not ticket or ticket.claimed_by:
                return
            guild = self.bot.get_guild(ticket.guild_id)
            if not guild:
                return
            channel = guild.get_channel(channel_id)
            category = guild.get_channel(category_id) if category_id else None
            if channel:
                with suppress(Exception):
                    await channel.delete(reason="Ticket unclaimed for 4h, auto-removed.")
            if category and isinstance(category, discord.CategoryChannel) and len(category.channels) == 0:
                with suppress(Exception):
                    await category.delete(reason="Temporary ticket category auto-removed.")
        finally:
            # Clean up task reference when done
            self.cleanup_tasks.pop(channel_id, None)

    def _cancel_cleanup_task(self, channel_id: int) -> None:
        """Cancel and remove cleanup task for a channel."""
        if (task := self.cleanup_tasks.pop(channel_id, None)) and not task.done():
            task.cancel()

    async def _ephemeral_success(self, send, ticket, ticket_channel):
        msg = await send(
            f"Ticket #{ticket.ticket_id} created successfully! Please check {ticket_channel.mention}",
            ephemeral=True,
        )
        if hasattr(msg, "delete"):
            await asyncio.sleep(10)
            with suppress(Exception):
                await msg.delete()

    @ticket.command(name="list")
    @app_commands.describe(user="User to list tickets for")
    @checks.has_pl(2)
    async def list(self, ctx: commands.Context, user: discord.Member):
        """List tickets involving a user."""
        # Support both prefix and slash (Interaction) usage
        if isinstance(ctx, commands.Context):
            guild = ctx.guild
            send = ctx.send
            author = ctx.author
        else:
            guild = ctx.guild
            send = ctx.response.send_message
            author = ctx.user

        await (
            ctx.response.defer(ephemeral=True)
            if hasattr(ctx, "response") and hasattr(ctx.response, "defer")
            else asyncio.sleep(0)
        )
        try:
            # Ensure guild config exists
            existing_config = await self.guild_config_controller.get_guild_config(guild.id)
            if not existing_config:
                await self.guild_config_controller.insert_guild_config(guild.id)

            target_user = user
            # Fetch all tickets for the guild
            all_tickets = await self.db.ticket.get_guild_tickets(guild.id)
            # Filter tickets where user is author
            user_tickets = [
                t
                for t in all_tickets
                if t.author_id == target_user.id or (hasattr(t, "participants") and target_user.id in t.participants)
            ]
            if not user_tickets:
                embed = EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedType.INFO,
                    user_name=author.display_name,
                    user_display_avatar=author.display_avatar.url,
                    title="No Tickets Found",
                    description=f"No tickets found for {target_user.display_name}.",
                )
                await send(embed=embed, ephemeral=True)
                return

            # Pagination logic
            page_size = 10
            total_pages = (len(user_tickets) + page_size - 1) // page_size
            current_page = 0

            async def send_page(page):
                embed = EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedType.INFO,
                    user_name=author.display_name,
                    user_display_avatar=author.display_avatar.url,
                    title=f"Tickets for {target_user.display_name}",
                    description=f"Page {page + 1}/{total_pages}",
                )
                for ticket in user_tickets[page * page_size : (page + 1) * page_size]:
                    ticket_author = guild.get_member(ticket.author_id)
                    author_name = ticket_author.display_name if ticket_author else f"Unknown ({ticket.author_id})"
                    claimed_info = ""
                    if ticket.claimed_by:
                        claimed_user = guild.get_member(ticket.claimed_by)
                        claimed_name = claimed_user.display_name if claimed_user else f"Unknown ({ticket.claimed_by})"
                        claimed_info = f" - Claimed by {claimed_name}"
                    status_emoji = {TicketStatus.OPEN: "🟢", TicketStatus.CLAIMED: "🟡", TicketStatus.CLOSED: "🔴"}.get(
                        ticket.status,
                        "❓",
                    )
                    channel = guild.get_channel(ticket.channel_id)
                    channel_info = channel.mention if channel else "Channel deleted"
                    embed.add_field(
                        name=f"{status_emoji} #{ticket.ticket_id} - {ticket.title}",
                        value=f"**Author:** {author_name}\n**Channel:** {channel_info}\n**Created:** <t:{int(ticket.created_at.timestamp())}:R>{claimed_info}",
                        inline=False,
                    )

                # Add navigation buttons if needed
                class TicketPaginator(discord.ui.View):
                    def __init__(self, parent, page):
                        super().__init__(timeout=60)
                        self.parent = parent
                        self.page = page

                    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, disabled=page == 0)
                    async def previous(self, interaction2: discord.Interaction, button: discord.ui.Button):
                        await interaction2.response.defer()
                        await send_page(self.page - 1)

                    @discord.ui.button(
                        label="Next",
                        style=discord.ButtonStyle.secondary,
                        disabled=page == total_pages - 1,
                    )
                    async def next(self, interaction2: discord.Interaction, button: discord.ui.Button):
                        await interaction2.response.defer()
                        await send_page(self.page + 1)

                view = TicketPaginator(self, page) if total_pages > 1 else discord.ui.View()
                if hasattr(ctx, "response") and ctx.response.is_done():
                    await ctx.followup.send(embed=embed, ephemeral=True, view=view)
                else:
                    await send(embed=embed, ephemeral=True, view=view)

            await send_page(current_page)
        except Exception as e:
            logger.error(f"Error listing tickets: {e}")
            await send("An error occurred while fetching tickets.", ephemeral=True)

    @commands.hybrid_command(name="ticket_list")
    @app_commands.describe(user="User to list tickets for")
    @checks.has_pl(2)
    async def ticket_list(self, ctx: commands.Context, user: discord.Member):
        """List tickets involving a user."""
        # Support both prefix and slash (Interaction) usage
        if isinstance(ctx, commands.Context):
            guild = ctx.guild
            send = ctx.send
            author = ctx.author
        else:
            guild = ctx.guild
            send = ctx.response.send_message
            author = ctx.user

        await (
            ctx.response.defer(ephemeral=True)
            if hasattr(ctx, "response") and hasattr(ctx.response, "defer")
            else asyncio.sleep(0)
        )
        try:
            # Ensure guild config exists
            existing_config = await self.guild_config_controller.get_guild_config(guild.id)
            if not existing_config:
                await self.guild_config_controller.insert_guild_config(guild.id)

            target_user = user
            # Fetch all tickets for the guild
            all_tickets = await self.db.ticket.get_guild_tickets(guild.id)
            # Filter tickets where user is author
            user_tickets = [
                t
                for t in all_tickets
                if t.author_id == target_user.id or (hasattr(t, "participants") and target_user.id in t.participants)
            ]
            if not user_tickets:
                embed = EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedType.INFO,
                    user_name=author.display_name,
                    user_display_avatar=author.display_avatar.url,
                    title="No Tickets Found",
                    description=f"No tickets found for {target_user.display_name}.",
                )
                await send(embed=embed, ephemeral=True)
                return

            # Pagination logic
            page_size = 10
            total_pages = (len(user_tickets) + page_size - 1) // page_size
            current_page = 0

            async def send_page(page):
                embed = EmbedCreator.create_embed(
                    bot=self.bot,
                    embed_type=EmbedType.INFO,
                    user_name=author.display_name,
                    user_display_avatar=author.display_avatar.url,
                    title=f"Tickets for {target_user.display_name}",
                    description=f"Page {page + 1}/{total_pages}",
                )
                for ticket in user_tickets[page * page_size : (page + 1) * page_size]:
                    ticket_author = guild.get_member(ticket.author_id)
                    author_name = ticket_author.display_name if ticket_author else f"Unknown ({ticket.author_id})"
                    claimed_info = ""
                    if ticket.claimed_by:
                        claimed_user = guild.get_member(ticket.claimed_by)
                        claimed_name = claimed_user.display_name if claimed_user else f"Unknown ({ticket.claimed_by})"
                        claimed_info = f" - Claimed by {claimed_name}"
                    status_emoji = {TicketStatus.OPEN: "🟢", TicketStatus.CLAIMED: "🟡", TicketStatus.CLOSED: "🔴"}.get(
                        ticket.status,
                        "❓",
                    )
                    channel = guild.get_channel(ticket.channel_id)
                    channel_info = channel.mention if channel else "Channel deleted"
                    embed.add_field(
                        name=f"{status_emoji} #{ticket.ticket_id} - {ticket.title}",
                        value=f"**Author:** {author_name}\n**Channel:** {channel_info}\n**Created:** <t:{int(ticket.created_at.timestamp())}:R>{claimed_info}",
                        inline=False,
                    )

                # Add navigation buttons if needed
                class TicketPaginator(discord.ui.View):
                    def __init__(self, parent, page):
                        super().__init__(timeout=60)
                        self.parent = parent
                        self.page = page

                    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, disabled=page == 0)
                    async def previous(self, interaction2: discord.Interaction, button: discord.ui.Button):
                        await interaction2.response.defer()
                        await send_page(self.page - 1)

                    @discord.ui.button(
                        label="Next",
                        style=discord.ButtonStyle.secondary,
                        disabled=page == total_pages - 1,
                    )
                    async def next(self, interaction2: discord.Interaction, button: discord.ui.Button):
                        await interaction2.response.defer()
                        await send_page(self.page + 1)

                view = TicketPaginator(self, page) if total_pages > 1 else discord.ui.View()
                if hasattr(ctx, "response") and ctx.response.is_done():
                    await ctx.followup.send(embed=embed, ephemeral=True, view=view)
                else:
                    await send(embed=embed, ephemeral=True, view=view)

            await send_page(current_page)
        except Exception as e:
            logger.error(f"Error listing tickets: {e}")
            await send("An error occurred while fetching tickets.", ephemeral=True)

    @ticket.command(name="stats")
    @app_commands.describe(user="Specific user to show stats for (optional)")
    @checks.has_pl(2)
    async def stats(self, ctx: commands.Context, user: discord.Member = None):
        """Show ticket statistics for staff members."""

        if isinstance(ctx, commands.Context):
            with suppress(discord.NotFound, discord.Forbidden, AttributeError):
                _ = ctx.message.delete()
            guild, author, is_prefix, send = ctx.guild, ctx.author, True, ctx.send
        else:
            guild, author, is_prefix = ctx.guild, ctx.user, False
            send = ctx.response.send_message if hasattr(ctx, "response") else (lambda *a, **k: None)
        if hasattr(ctx, "response") and hasattr(ctx.response, "defer"):
            await ctx.response.defer(ephemeral=True)

        try:
            all_tickets, claims_count, closed_count = await self._gather_guild_ticket_metrics(guild.id)
            embed = self._build_stats_embed(author, user, guild, all_tickets, claims_count, closed_count)

            if is_prefix:
                await self._ephemeral_msg(ctx, embed)
            elif hasattr(ctx, "response") and ctx.response.is_done():
                await ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await ctx.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error showing ticket stats: {e}")
            msg = "An error occurred while fetching ticket statistics."
            if is_prefix:
                await self._ephemeral_msg(ctx, msg)
            elif hasattr(ctx, "followup") and hasattr(ctx, "response") and ctx.response.is_done():
                await ctx.followup.send(msg, ephemeral=True)
            else:
                await send(msg, ephemeral=True)

    @ticket.command(name="leaderboard")
    @app_commands.describe(
        metric="What to rank by: 'claims', 'closed', or 'rate' (default: claims)",
        limit="Number of users to show (default: 10)",
    )
    @checks.has_pl(2)
    async def leaderboard(self, ctx: commands.Context, metric: str = "claims", limit: int = 10):
        """Show ticket activity leaderboard for staff."""

        if isinstance(ctx, commands.Context):
            guild, author, send = ctx.guild, ctx.author, ctx.send
        else:
            guild, author, send = ctx.guild, ctx.user, ctx.response.send_message

        if hasattr(ctx, "response") and hasattr(ctx.response, "defer"):
            await ctx.response.defer(ephemeral=True)

        try:
            tickets = await self.db.ticket.get_guild_tickets(guild.id, limit=1000)
            embed = self._build_leaderboard_embed(author, guild, tickets, metric, limit)
            if hasattr(ctx, "response") and ctx.response.is_done():
                await ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}")
            await send("An error occurred while generating the leaderboard.", ephemeral=True)

    @ticket.command(name="add")
    @app_commands.describe(target="User or role to add")
    @checks.has_pl(2)
    async def add(self, ctx: commands.Context, target: str):
        """Add a user or role to the current ticket channel (Staff only)."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await self._ephemeral_msg(ctx, "This command can only be used in a ticket channel.")
            # Privacy: delete user's command message
            if isinstance(ctx, commands.Context):
                with suppress(discord.NotFound, discord.Forbidden):
                    await ctx.message.delete()
            return

        ticket = await self.db.ticket.get_ticket_by_channel(ctx.channel.id)
        if not ticket:
            await self._ephemeral_msg(ctx, "This is not a valid ticket channel.")
            # Privacy: delete user's command message
            if isinstance(ctx, commands.Context):
                with suppress(discord.NotFound, discord.Forbidden):
                    await ctx.message.delete()
            return

        # Support @role mention
        if target.startswith("<@&") and target.endswith(">"):
            role_id = target[3:-1]
            target_obj = ctx.guild.get_role(int(role_id)) if role_id.isdigit() else None  # SIM108
        else:
            target_obj = self._resolve_target(ctx, target)

        if not target_obj:
            await self._ephemeral_msg(ctx, f"Could not find user or role for '{target}'.")
            # Privacy: delete user's command message
            if isinstance(ctx, commands.Context):
                with suppress(discord.NotFound, discord.Forbidden):
                    await ctx.message.delete()
            return

        await ctx.channel.set_permissions(
            target_obj,
            view_channel=True,
            send_messages=True,
            read_messages=True,
            reason="Added to ticket by staff",
        )

        if ticket_log_cog := self.bot.get_cog("TicketLog"):
            actor_id = ctx.author.id if hasattr(ctx, "author") else ctx.user.id
            event_type = "ROLE_ADDED" if isinstance(target_obj, discord.Role) else "USER_ADDED"
            target_name = getattr(target_obj, "name", str(target_obj))
            ticket_log_cog.add_ticket_event(ctx.channel.id, event_type, actor_id, f"Added {target_name} to ticket")
        await self._ephemeral_msg(
            ctx,
            f"{getattr(target_obj, 'mention', str(target_obj))} has been added to this ticket.",
        )
        # Privacy: delete user's command message
        if isinstance(ctx, commands.Context):
            with suppress(discord.NotFound, discord.Forbidden):
                await ctx.message.delete()

    @ticket.command(name="remove")
    @app_commands.describe(target="User or role to remove (@mention or name)")
    @checks.has_pl(2)
    async def remove(self, ctx: commands.Context, target: str):
        """Remove a user or role from the ticket (Staff only)."""
        valid, ticket = await self._validate_ticket_channel(ctx)
        if not valid:
            return
        target_obj = self._parse_target(ctx, target)
        if not target_obj:
            await self._ephemeral_msg(ctx, f"Could not find user or role for '{target}'.")
            await self._maybe_delete_command_message(ctx)
            return

        await self._log_removal_event(ctx, target_obj)
        await self._perform_removal(ctx, target_obj)
        await self._maybe_delete_command_message(ctx)

    async def _log_removal_event(self, ctx, target_obj):
        """Log the removal event to ticket log."""
        if ticket_log_cog := self.bot.get_cog("TicketLog"):
            actor_id = ctx.author.id if hasattr(ctx, "author") else ctx.user.id
            event_type = "ROLE_REMOVED" if isinstance(target_obj, discord.Role) else "USER_REMOVED"
            target_name = getattr(target_obj, "name", str(target_obj))
            ticket_log_cog.add_ticket_event(ctx.channel.id, event_type, actor_id, f"Removed {target_name} from ticket")

    async def _perform_removal(self, ctx, target_obj):
        """Remove the target object from the ticket channel."""
        if isinstance(target_obj, discord.Role):
            await ctx.channel.set_permissions(target_obj, overwrite=None, reason="Removed role from ticket by staff")
            # Remove all members of the role from the channel
            for member in target_obj.members:
                await ctx.channel.set_permissions(
                    member,
                    overwrite=None,
                    reason="Removed from ticket (role removal by staff)",
                )
            await self._ephemeral_msg(ctx, f"{target_obj.mention} and its members have been removed from this ticket.")
        else:
            await ctx.channel.set_permissions(target_obj, overwrite=None, reason="Removed from ticket by staff")
            await self._ephemeral_msg(
                ctx,
                f"{getattr(target_obj, 'mention', str(target_obj))} has been removed from this ticket.",
            )

    async def _gather_guild_ticket_metrics(self, guild_id: int):
        tickets = await self.db.ticket.get_guild_tickets(guild_id, limit=1000)
        claims_count: dict[int, int] = defaultdict(int)
        closed_count: dict[int, int] = defaultdict(int)
        for t in tickets:
            cid = t.claimed_by
            if not cid:
                continue
            claims_count[cid] += 1
            if t.status == TicketStatus.CLOSED:
                closed_count[cid] += 1
        return tickets, claims_count, closed_count

    def _build_stats_embed(self, author, user, guild, tickets, claims_count, closed_count):
        def _base(title: str):
            return EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedType.INFO,
                user_name=author.display_name,
                user_display_avatar=author.display_avatar.url,
                title=title,
                description="All-time statistics",
            )

        if user:
            embed = _base(f"Ticket Stats for {user.display_name}")
            claims = claims_count.get(user.id, 0)
            closed = closed_count.get(user.id, 0)
            rate = f"{(closed / claims * 100):.1f}%" if claims else "N/A"
            for name, val in (("🎫 Tickets Claimed", claims), ("✅ Tickets Closed", closed), ("📊 Close Rate", rate)):
                embed.add_field(name=name, value=str(val), inline=True)
        else:
            embed = _base("Staff Ticket Statistics")
            if not claims_count:
                embed.add_field(name="No Data", value="No ticket claims found for this period.", inline=False)
            else:
                staff_activity = [
                    (member := guild.get_member(uid), claim_count, closed_count.get(uid, 0))
                    for uid, claim_count in claims_count.items()
                    if (guild.get_member(uid) is not None)
                ]
                staff_activity.sort(key=lambda x: x[1], reverse=True)
                for i, (member, claims, closed) in enumerate(staff_activity[:10]):
                    rate = (closed / claims * 100) if claims else 0
                    embed.add_field(
                        name=f"#{i + 1} {member.display_name}",
                        value=f"🎫 {claims} claimed\n✅ {closed} closed\n📊 {rate:.1f}% rate",
                        inline=True,
                    )
        total_tickets = len(tickets)
        total_claimed = sum(1 for t in tickets if t.claimed_by)
        total_closed = sum(1 for t in tickets if t.status == TicketStatus.CLOSED)
        embed.add_field(
            name="📈 Server Summary",
            value=f"Total: {total_tickets}\nClaimed: {total_claimed}\nClosed: {total_closed}",
            inline=True,
        )
        return embed

    def _build_leaderboard_embed(self, author, guild, tickets, metric: str, limit: int):
        claims_count: dict[int, int] = defaultdict(int)
        closed_count: dict[int, int] = defaultdict(int)
        for t in tickets:
            cid = t.claimed_by
            if not cid:
                continue
            claims_count[cid] += 1
            if t.status == TicketStatus.CLOSED:
                closed_count[cid] += 1
        if not claims_count:
            return EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedType.INFO,
                user_name=author.display_name,
                user_display_avatar=author.display_avatar.url,
                title="Ticket Leaderboard",
                description="No ticket activity found for this period.",
            )

        def score(c, cl):
            rate = (cl / c * 100) if c else 0
            return {"claims": c, "closed": cl, "rate": rate}.get(metric, c), rate

        staff = []
        for uid, c in claims_count.items():
            member = guild.get_member(uid)
            if not member:
                continue
            cl = closed_count.get(uid, 0)
            sc, rate = score(c, cl)
            staff.append((member, c, cl, rate, sc))
        staff.sort(key=lambda x: x[4], reverse=True)
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedType.INFO,
            user_name=author.display_name,
            user_display_avatar=author.display_avatar.url,
            title=f"Ticket Leaderboard - {metric.title()}",
            description=f"Top {min(limit, len(staff))} staff members (all-time)",
        )
        medals = ["🥇", "🥈", "🥉"]
        for i, (member, c, cl, rate, _sc) in enumerate(staff[:limit]):
            medal = medals[i] if i < 3 else f"#{i + 1}"
            match metric:
                case "claims":
                    value = f"🎫 {c} tickets claimed"
                case "closed":
                    value = f"✅ {cl} tickets closed"
                case "rate":
                    value = f"📊 {rate:.1f}% close rate ({cl}/{c})"
                case _:
                    value = f"🎫 {c} claims • ✅ {cl} closed"
            embed.add_field(name=f"{medal} {member.display_name}", value=value, inline=False)
        return embed

    async def _validate_ticket_channel(self, ctx):
        if not isinstance(ctx.channel, discord.TextChannel):
            await self._ephemeral_msg(ctx, "This command can only be used in a ticket channel.")
            await self._maybe_delete_command_message(ctx)
            return False, None
        ticket = await self.db.ticket.get_ticket_by_channel(ctx.channel.id)
        if not ticket:
            await self._ephemeral_msg(ctx, "This is not a valid ticket channel.")
            await self._maybe_delete_command_message(ctx)
            return False, None
        return True, ticket

    def _parse_target(self, ctx, target: str):
        if target.startswith("<@&") and target.endswith(">"):
            role_id = target.strip("<@&>")
            return ctx.guild.get_role(int(role_id)) if role_id.isdigit() else None
        return self._resolve_target(ctx, target)

    async def _maybe_delete_command_message(self, ctx):
        if isinstance(ctx, commands.Context):
            with suppress(discord.NotFound, discord.Forbidden):
                await ctx.message.delete()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.add_view(TicketManagementView(self.bot))


async def setup(bot: Tux) -> None:
    """Setup the Tickets cog."""
    await bot.add_cog(Tickets(bot))
