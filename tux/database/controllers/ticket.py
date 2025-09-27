"""Ticket database controller for managing support tickets."""

from datetime import UTC, datetime

from loguru import logger

from prisma.enums import TicketStatus
from prisma.models import Ticket
from tux.database.controllers.base import BaseController


class TicketController(BaseController[Ticket]):
    """Controller for managing ticket database operations."""

    def __init__(self) -> None:
        super().__init__("ticket")

    async def create_ticket(
        self,
        guild_id: int,
        channel_id: int,
        author_id: int,
        title: str,
    ) -> Ticket | None:
        """
        Create a new ticket in the database.

        Parameters
        ----------
        guild_id : int
            The ID of the guild where the ticket was created.
        channel_id : int
            The ID of the ticket channel.
        author_id : int
            The ID of the user who created the ticket.
        title : str
            The title/subject of the ticket.

        Returns
        -------
        Ticket | None
            The created ticket object or None if creation failed.
        """
        try:
            return await self.create(
                data={
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "author_id": author_id,
                    "title": title,
                    "status": TicketStatus.OPEN,
                },
            )
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            return None

    async def claim_ticket(self, channel_id: int, moderator_id: int) -> Ticket | None:
        """
        Claim a ticket for a moderator.

        Parameters
        ----------
        channel_id : int
            The ID of the ticket channel.
        moderator_id : int
            The ID of the moderator claiming the ticket.

        Returns
        -------
        Ticket | None
            The updated ticket object or None if update failed.
        """
        try:
            return await self.update(
                where={"channel_id": channel_id},
                data={
                    "claimed_by": moderator_id,
                    "status": TicketStatus.CLAIMED,
                },
            )
        except Exception as e:
            logger.error(f"Failed to claim ticket {channel_id}: {e}")
            return None

    async def unclaim_ticket(self, channel_id: int) -> Ticket | None:
        """
        Unclaim a ticket, resetting it to open status.

        Parameters
        ----------
        channel_id : int
            The ID of the ticket channel.

        Returns
        -------
        Ticket | None
            The updated ticket object or None if update failed.
        """
        try:
            return await self.update(
                where={"channel_id": channel_id},
                data={
                    "claimed_by": None,
                    "status": TicketStatus.OPEN,
                },
            )
        except Exception as e:
            logger.error(f"Failed to unclaim ticket {channel_id}: {e}")
            return None

    async def close_ticket(self, channel_id: int) -> Ticket | None:
        """
        Close a ticket.

        Parameters
        ----------
        channel_id : int
            The ID of the ticket channel.

        Returns
        -------
        Ticket | None
            The updated ticket object or None if update failed.
        """
        try:
            return await self.update(
                where={"channel_id": channel_id},
                data={
                    "status": TicketStatus.CLOSED,
                    "closed_at": datetime.now(UTC),
                },
            )
        except Exception as e:
            logger.error(f"Failed to close ticket {channel_id}: {e}")
            return None

    async def get_ticket_by_channel(self, channel_id: int) -> Ticket | None:
        """
        Get a ticket by its channel ID.

        Parameters
        ----------
        channel_id : int
            The ID of the ticket channel.

        Returns
        -------
        Ticket | None
            The ticket object or None if not found.
        """
        try:
            return await self.find_one(where={"channel_id": channel_id})
        except Exception as e:
            logger.error(f"Failed to get ticket by channel {channel_id}: {e}")
            return None

    async def get_guild_tickets(
        self,
        guild_id: int,
        status: TicketStatus | None = None,
        limit: int = 50,
    ) -> list[Ticket]:
        """
        Get tickets for a guild, optionally filtered by status.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.
        status : TicketStatus | None, optional
            Filter by ticket status, by default None (all statuses).
        limit : int, optional
            Maximum number of tickets to return, by default 50.

        Returns
        -------
        list[Ticket]
            List of ticket objects.
        """
        try:
            where_clause = {"guild_id": guild_id}
            if status:
                where_clause["status"] = status

            return await self.find_many(where=where_clause, take=limit, order={"created_at": "desc"}) or []
        except Exception as e:
            logger.error(f"Failed to get guild tickets for {guild_id}: {e}")
            return []

    async def get_user_tickets(
        self,
        guild_id: int,
        user_id: int,
        status: TicketStatus | None = None,
    ) -> list[Ticket]:
        """
        Get tickets created by a specific user.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.
        user_id : int
            The ID of the user.
        status : TicketStatus | None, optional
            Filter by ticket status, by default None (all statuses).

        Returns
        -------
        list[Ticket]
            List of ticket objects.
        """
        try:
            where_clause = {"guild_id": guild_id, "author_id": user_id}
            if status:
                where_clause["status"] = status

            return await self.find_many(where=where_clause, order={"created_at": "desc"}) or []
        except Exception as e:
            logger.error(f"Failed to get user tickets for {user_id} in {guild_id}: {e}")
            return []

    async def delete_ticket(self, channel_id: int) -> bool:
        """
        Delete a ticket from the database.

        Parameters
        ----------
        channel_id : int
            The ID of the ticket channel.

        Returns
        -------
        bool
            True if deletion was successful, False otherwise.
        """
        try:
            await self.delete(where={"channel_id": channel_id})
        except Exception as e:
            logger.error(f"Failed to delete ticket {channel_id}: {e}")
            return False
        else:
            return True
