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
        # Early return if no log configuration
        if not (log_cog := self.bot.get_cog("TicketLogConfig")):
            return False

        if not (log_channel_id := await log_cog.get_log_channel_id(guild.id)):
            return False

        if not (log_channel := guild.get_channel(log_channel_id)):
            return False

        # Generate transcript content
        transcript_content = self._generate_transcript_content(guild, channel, ticket, messages)

        # Create and send the transcript
        file = discord.File(io.BytesIO(transcript_content.encode()), filename=f"transcript_{channel.id}.txt")
        embed = self._create_transcript_embed(guild, ticket, messages)

        await log_channel.send(embed=embed, file=file)
        self.clear_ticket_events(channel.id)
        return True

    def _generate_transcript_content(self, guild, channel, ticket, messages):
        """Generate the complete transcript content."""
        tracked_events = self.get_ticket_events(channel.id)
        all_entries = self._combine_messages_and_events(messages, tracked_events)
        lines = self._format_transcript_lines(guild, all_entries)
        metadata_lines = self._create_metadata_lines(guild, ticket, channel)
        return "\n".join(metadata_lines + lines)

    def _combine_messages_and_events(self, messages, tracked_events):
        """Combine messages and events, sorted by timestamp."""
        all_entries = [{"timestamp": msg.created_at, "type": "message", "data": msg} for msg in messages] + [
            {"timestamp": event["timestamp"], "type": "event", "data": event} for event in tracked_events
        ]
        return sorted(all_entries, key=lambda x: x["timestamp"])

    def _format_transcript_lines(self, guild, all_entries):
        """Format all entries into transcript lines."""
        lines = []
        for entry in all_entries:
            timestamp_str = entry["timestamp"].strftime("%Y-%m-%d %H:%M")

            if entry["type"] == "message":
                line = self._format_message_line(timestamp_str, entry["data"])
            else:  # event
                line = self._format_event_line(timestamp_str, guild, entry["data"])

            lines.append(line)
        return lines

    def _format_message_line(self, timestamp_str, msg):
        """Format a message into a transcript line."""
        author = f"{msg.author.display_name} ({msg.author.id})"
        tags = self._analyze_message_content(msg.content, msg)
        tag_str = "".join(f"[{tag}] " for tag in tags)
        return f"[{timestamp_str}] {author}: {tag_str}{msg.content}"

    def _format_event_line(self, timestamp_str, guild, event):
        """Format an event into a transcript line."""
        if user := guild.get_member(event["user_id"]):
            user_name = user.display_name
        else:
            user_name = f"Unknown ({event['user_id']})"

        event_msg = self._format_event_message(event, user_name)
        return f"[{timestamp_str}] SYSTEM: [EVENT] {event_msg}"

    def _create_metadata_lines(self, guild, ticket, channel):
        """Create the metadata header for the transcript."""
        if author := guild.get_member(ticket.author_id):
            author_name = author.display_name
        else:
            author_name = f"Unknown ({ticket.author_id})"

        if ticket.claimed_by and (claimed_user := guild.get_member(ticket.claimed_by)):
            claimed_by = claimed_user.display_name
        else:
            claimed_by = "None"

        return [
            f"=== TICKET #{ticket.ticket_id} TRANSCRIPT ===",
            f"Title: {ticket.title}",
            f"Author: {author_name}",
            f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"Channel: #{channel.name} ({channel.id})",
            f"Status: {ticket.status.value if hasattr(ticket.status, 'value') else ticket.status}",
            f"Claimed by: {claimed_by}",
            "=" * 50,
            "",
        ]

    def _create_transcript_embed(self, guild, ticket, messages):
        """Create the summary embed for the transcript."""
        author_display = author.mention if (author := guild.get_member(ticket.author_id)) else "Unknown User"

        embed = discord.Embed(
            title=f"Ticket #{ticket.ticket_id} Transcript",
            description=f"**Title:** {ticket.title}\n**Author:** {author_display}",
            color=0x2ECC71 if ticket.status == TicketStatus.CLOSED else 0xE74C3C,
            timestamp=datetime.now(UTC),
        )

        tracked_events = self.get_ticket_events(ticket.channel_id) if hasattr(ticket, "channel_id") else []
        embed.add_field(name="Messages", value=str(len(messages)), inline=True)
        embed.add_field(name="Events", value=str(len(tracked_events)), inline=True)
        embed.add_field(
            name="Status",
            value=ticket.status.value if hasattr(ticket.status, "value") else str(ticket.status),
            inline=True,
        )

        if ticket.claimed_by and (claimed_user := guild.get_member(ticket.claimed_by)):
            embed.add_field(
                name="Claimed By",
                value=claimed_user.mention,
                inline=True,
            )

        return embed

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
