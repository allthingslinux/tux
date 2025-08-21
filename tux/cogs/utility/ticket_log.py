import io
from datetime import UTC, datetime

import discord
from discord.ext import commands

from prisma.enums import TicketStatus
from tux.bot import Tux


class TicketLog(commands.Cog):
    """Cog to handle ticket transcript logging with enhanced event tracking."""

    def __init__(self, bot: Tux):
        self.bot = bot
        # Track ticket events that happen outside of message content
        self.ticket_events = {}  # {channel_id: [events]}

    def add_ticket_event(self, channel_id: int, event_type: str, user_id: int, details: str | None = None):
        """Add a ticket event to track for logging."""
        if channel_id not in self.ticket_events:
            self.ticket_events[channel_id] = []

        event = {
            "timestamp": datetime.now(UTC),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        }
        self.ticket_events[channel_id].append(event)

    def get_ticket_events(self, channel_id: int):
        """Get all events for a ticket channel."""
        return self.ticket_events.get(channel_id, [])

    def clear_ticket_events(self, channel_id: int):
        """Clear events for a ticket channel after logging."""
        if channel_id in self.ticket_events:
            del self.ticket_events[channel_id]

    async def log_transcript(self, guild, channel, ticket, messages):
        """Log the transcript as a plain text file with enhanced event detection."""
        log_cog = self.bot.get_cog("TicketLogConfig")
        log_channel_id = None
        if log_cog:
            log_channel_id = log_cog.get_log_channel_id(guild.id)

        if log_channel_id:
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                # Get tracked events for this channel
                tracked_events = self.get_ticket_events(channel.id)

                # Combine messages and tracked events, then sort by timestamp
                all_entries = [{"timestamp": msg.created_at, "type": "message", "data": msg} for msg in messages] + [
                    {"timestamp": event["timestamp"], "type": "event", "data": event} for event in tracked_events
                ]

                # Sort by timestamp
                all_entries.sort(key=lambda x: x["timestamp"])

                lines = []
                for entry in all_entries:
                    timestamp_str = entry["timestamp"].strftime("%Y-%m-%d %H:%M")

                    if entry["type"] == "message":
                        msg = entry["data"]
                        author = f"{msg.author.display_name} ({msg.author.id})"
                        content = msg.content

                        # Enhanced message content analysis
                        tags = self._analyze_message_content(content, msg)
                        tag_str = "".join(f"[{tag}] " for tag in tags)

                        lines.append(f"[{timestamp_str}] {author}: {tag_str}{content}")

                    elif entry["type"] == "event":
                        event = entry["data"]
                        user = guild.get_member(event["user_id"])
                        user_name = user.display_name if user else f"Unknown ({event['user_id']})"

                        event_msg = self._format_event_message(event, user_name)
                        lines.append(f"[{timestamp_str}] SYSTEM: [EVENT] {event_msg}")

                # Add ticket metadata at the beginning
                metadata_lines = [
                    f"=== TICKET #{ticket.ticket_id} TRANSCRIPT ===",
                    f"Title: {ticket.title}",
                    f"Author: {guild.get_member(ticket.author_id).display_name if guild.get_member(ticket.author_id) else f'Unknown ({ticket.author_id})'}",
                    f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    f"Channel: #{channel.name} ({channel.id})",
                    f"Status: {ticket.status.value if hasattr(ticket.status, 'value') else ticket.status}",
                    f"Claimed by: {guild.get_member(ticket.claimed_by).display_name if ticket.claimed_by and guild.get_member(ticket.claimed_by) else 'None'}",
                    "=" * 50,
                    "",
                ]

                transcript_text = "\n".join(metadata_lines + lines)
                file = discord.File(io.BytesIO(transcript_text.encode()), filename=f"transcript_{channel.id}.txt")

                # Create summary embed
                embed = discord.Embed(
                    title=f"Ticket #{ticket.ticket_id} Transcript",
                    description=f"**Title:** {ticket.title}\n**Author:** {guild.get_member(ticket.author_id).mention if guild.get_member(ticket.author_id) else 'Unknown User'}",
                    color=0x2ECC71 if ticket.status == TicketStatus.CLOSED else 0xE74C3C,
                    timestamp=datetime.now(UTC),
                )
                embed.add_field(name="Messages", value=str(len(messages)), inline=True)
                embed.add_field(name="Events", value=str(len(tracked_events)), inline=True)
                embed.add_field(
                    name="Status",
                    value=ticket.status.value if hasattr(ticket.status, "value") else str(ticket.status),
                    inline=True,
                )

                if ticket.claimed_by:
                    claimed_user = guild.get_member(ticket.claimed_by)
                    embed.add_field(
                        name="Claimed By",
                        value=claimed_user.mention if claimed_user else f"Unknown ({ticket.claimed_by})",
                        inline=True,
                    )

                await log_channel.send(embed=embed, file=file)

                # Clear tracked events after logging
                self.clear_ticket_events(channel.id)
                return True
        return False

    def _analyze_message_content(self, content: str, msg: discord.Message) -> list:
        """Analyze message content for ticket-related events."""
        tags = []
        content_lower = content.lower()

        # Bot/system messages
        if msg.author.bot:
            if any(
                phrase in content_lower for phrase in ["ticket closed", "has been closed", "ticket has been closed"]
            ):
                tags.append("TICKET CLOSED")
            elif any(
                phrase in content_lower for phrase in ["ticket created", "ticket opened", "thank you for creating"]
            ):
                tags.append("TICKET CREATED")
            elif "claimed this ticket" in content_lower:
                tags.append("TICKET CLAIMED")
            elif "unclaimed this ticket" in content_lower:
                tags.append("TICKET UNCLAIMED")

        # User messages
        elif any(phrase in content_lower for phrase in ["requested to close", "request close", "please close"]):
            tags.append("CLOSE REQUESTED")
        elif any(phrase in content_lower for phrase in ["/close", "!close", "$close"]):
            tags.append("CLOSE COMMAND")

        # Check for embeds that might contain ticket info
        if msg.embeds:
            for embed in msg.embeds:
                if embed.title:
                    title_lower = embed.title.lower()
                    if "ticket" in title_lower and "closed" in title_lower:
                        tags.append("TICKET CLOSED")
                    elif "ticket" in title_lower and "claimed" in title_lower:
                        tags.append("TICKET CLAIMED")

        return tags

    def _format_event_message(self, event: dict, user_name: str) -> str:
        """Format an event into a readable message."""
        event_type = event["event_type"]
        details = event.get("details", "")
        mapping = {
            "TICKET_CLAIMED": f"{user_name} claimed the ticket. {details}",
            "TICKET_UNCLAIMED": f"{user_name} unclaimed the ticket. {details}",
            "TICKET_CLOSED": f"{user_name} closed the ticket. {details}",
            "TICKET_REOPENED": f"{user_name} reopened the ticket. {details}",
            "USER_ADDED": f"{user_name} was added to the ticket. {details}",
            "USER_REMOVED": f"{user_name} was removed from the ticket. {details}",
            "ROLE_ADDED": f"Role was added to the ticket by {user_name}. {details}",
            "ROLE_REMOVED": f"Role was removed from the ticket by {user_name}. {details}",
            "PERMISSIONS_CHANGED": f"{user_name} changed ticket permissions. {details}",
            "CLOSE_REQUESTED": f"{user_name} requested to close the ticket. {details}",
        }
        return mapping.get(event_type, f"{user_name} performed action: {event_type}. {details}").strip()


async def setup(bot: Tux):
    await bot.add_cog(TicketLog(bot))
