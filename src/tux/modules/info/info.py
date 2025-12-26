"""
Information display commands for Discord objects.

This module provides comprehensive information display commands for various Discord
entities including users, members, channels, guilds, roles, emojis, and stickers.
Each command shows detailed information in an organized embed format.
"""

import contextlib
from collections.abc import Awaitable, Callable, Generator, Iterable, Iterator
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands
from discord.utils import TimestampStyle
from reactionmenu import ViewButton, ViewMenu

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.constants import BANS_LIMIT
from tux.ui.embeds import EmbedCreator, EmbedType


class Info(BaseCog):
    """Information commands for Discord objects."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Info cog with type handlers.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        self._type_handlers: dict[
            type,
            Callable[[commands.Context[Tux], Any], Awaitable[None]],
        ] = {
            discord.Member: self._show_member_info,
            discord.User: self._show_user_info,
            discord.Message: self._show_message_info,
            discord.abc.GuildChannel: self._show_channel_info,
            discord.Guild: self._show_guild_info,
            discord.Role: self._show_role_info,
            discord.Emoji: self._show_emoji_info,
            discord.GuildSticker: self._show_sticker_info,
            discord.Invite: self._show_invite_info,
            discord.Thread: self._show_thread_info,
            discord.ScheduledEvent: self._show_event_info,
        }

    @staticmethod
    def _format_bool(value: bool) -> str:
        """
        Convert boolean to checkmark/cross emoji.

        Returns
        -------
        str
            ✅ for True, ❌ for False.
        """
        return "✅" if value else "❌"

    @staticmethod
    def _format_datetime(dt: datetime | None, style: TimestampStyle = "R") -> str:
        """
        Format datetime to Discord relative format or fallback.

        Returns
        -------
        str
            Formatted Discord timestamp or "Unknown" if None.
        """
        if dt is None:
            return "Unknown"
        try:
            return discord.utils.format_dt(dt, style)
        except (TypeError, ValueError):
            return "Unknown"

    def _create_info_embed(
        self,
        title: str,
        description: str | None = None,
        *,
        thumbnail_url: str | None = None,
        image_url: str | None = None,
        footer_text: str | None = None,
        footer_icon_url: str | None = None,
        author_text: str | None = None,
        author_icon_url: str | None = None,
        custom_color: discord.Color | None = None,
    ) -> discord.Embed:
        """
        Create a standardized info embed.

        Returns
        -------
        discord.Embed
            The created embed.
        """
        return EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
            image_url=image_url,
            custom_color=custom_color or discord.Color.blurple(),
            custom_footer_text=footer_text,
            custom_footer_icon_url=footer_icon_url,
            custom_author_text=author_text,
            custom_author_icon_url=author_icon_url,
        )

    @commands.hybrid_group(
        name="info",
        aliases=["i"],
    )
    @commands.guild_only()
    async def info(
        self,
        ctx: commands.Context[Tux],
        entity: str | None = None,
    ) -> None:
        """Get information about a Discord object by ID or mention.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object associated with the command.
        entity : str | None
            The entity to get information about (member, user, message, channel, role, emoji, sticker, invite, thread, event, etc.), or None for help.
        """
        if entity is None:
            await ctx.send_help("info")
            return

        # Try different converters to determine the object type
        # Note: We try member/user/channel/role/etc FIRST before guild IDs
        # because member/user IDs are the same length as guild IDs (17-19 digits),
        # and users are more likely to query members/users than other guilds
        # Note: InviteConverter is skipped for very short strings that can't be valid invite codes
        # Discord invite codes are typically 7-8 characters, minimum 6 characters
        converters: list[commands.Converter[Any]] = [
            commands.MemberConverter(),
            commands.UserConverter(),
            commands.MessageConverter(),
            commands.GuildChannelConverter(),
            commands.RoleConverter(),
            commands.EmojiConverter(),
            commands.GuildStickerConverter(),
        ]

        # Only add InviteConverter if the entity looks like it could be an invite code
        # Discord invite codes are minimum 6 characters (vanity URLs can be longer)
        if (
            len(entity) >= 6
            or "discord.gg/" in entity.lower()
            or "discord.com/invite/" in entity.lower()
        ):
            converters.append(commands.InviteConverter())

        converters.extend(
            [
                commands.ThreadConverter(),
                commands.ScheduledEventConverter(),
            ],
        )

        for converter in converters:
            try:
                converted = await converter.convert(ctx, entity)
                # Find the handler for this type
                for handler_type, handler in self._type_handlers.items():
                    if isinstance(converted, handler_type):
                        # Skip @everyone role if it conflicts with guild ID
                        if (
                            isinstance(converted, discord.Role)
                            and converted.name == "@everyone"
                        ):
                            continue
                        await handler(ctx, converted)
                        return
            except commands.BadArgument:
                continue

        # Special handling for potential guild IDs (check last to avoid conflicts with member/user IDs)
        # Only check if it looks like a guild ID AND none of the other converters worked
        if (
            entity.isdigit() and 15 <= len(entity) <= 20
        ):  # Guild IDs are typically 17-19 digits
            with contextlib.suppress(ValueError):
                guild_id = int(entity)
                # Check if bot is in this guild
                guild = self.bot.get_guild(guild_id)
                if guild is not None:
                    await self._show_guild_info(ctx, guild)
                    return  # Exit here, don't try other converters
                # Valid guild ID format but bot not in guild
                await ctx.send(
                    f"❌ I'm not in a server with ID `{entity}`. I can only show information for servers I'm a member of.",
                )
                return  # Exit here, don't try other converters

        # If no converter worked, show error
        # Since this is @commands.guild_only(), ctx.guild should never be None at runtime
        # But we need to satisfy the type checker
        guild = ctx.guild
        if guild and hasattr(self.bot, "prefix_manager") and self.bot.prefix_manager:
            prefix = await self.bot.prefix_manager.get_prefix(guild.id)
        else:
            prefix = "$"
        await ctx.send(
            f"❌ I couldn't find information about '{entity}'. Use `{prefix}info` without arguments to see available options.",
        )

    async def _show_guild_info(
        self,
        ctx: commands.Context[Tux],
        guild: discord.Guild,
    ) -> None:
        """Show information about a guild/server."""
        embed = (
            self._create_info_embed(
                title=guild.name,
                description=guild.description or "No description available.",
                thumbnail_url=guild.icon.url if guild.icon else None,
                footer_text=f"ID: {guild.id} | Created: {guild.created_at.strftime('%B %d, %Y')}",
            )
            .add_field(
                name="Owner",
                value=str(guild.owner.mention) if guild.owner else "Unknown",
            )
            .add_field(name="Vanity URL", value=guild.vanity_url_code or "None")
            .add_field(name="Boosts", value=guild.premium_subscription_count)
            .add_field(name="Text Channels", value=len(guild.text_channels))
            .add_field(name="Voice Channels", value=len(guild.voice_channels))
            .add_field(name="Forum Channels", value=len(guild.forums))
            .add_field(
                name="Emojis",
                value=f"{len(guild.emojis)}/{2 * guild.emoji_limit}",
            )
            .add_field(
                name="Stickers",
                value=f"{len(guild.stickers)}/{guild.sticker_limit}",
            )
            .add_field(name="Roles", value=len(guild.roles))
            .add_field(
                name="Humans",
                value=sum(not member.bot for member in guild.members),
            )
            .add_field(name="Bots", value=sum(member.bot for member in guild.members))
            .add_field(
                name="Bans",
                value=len([entry async for entry in guild.bans(limit=BANS_LIMIT)]),
            )
        )

        await ctx.send(embed=embed)

    async def _show_member_info(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
    ) -> None:
        """
        Show information about a member.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        member : discord.Member
            The member to get information about.
        """
        user = await self.bot.fetch_user(member.id)
        embed = (
            self._create_info_embed(
                title=member.display_name,
                description="Here is some information about the member.",
                thumbnail_url=member.display_avatar.url,
                image_url=user.banner.url if user.banner else None,
            )
            .add_field(name="Bot?", value=self._format_bool(member.bot), inline=False)
            .add_field(name="Username", value=member.name, inline=False)
            .add_field(name="ID", value=str(member.id), inline=False)
            .add_field(
                name="Joined",
                value=self._format_datetime(member.joined_at),
                inline=False,
            )
            .add_field(
                name="Registered",
                value=self._format_datetime(member.created_at),
                inline=False,
            )
            .add_field(
                name="Roles",
                value=", ".join(role.mention for role in member.roles[1:])
                if member.roles[1:]
                else "No roles",
                inline=False,
            )
        )

        await ctx.send(embed=embed)

    async def _show_user_info(
        self,
        ctx: commands.Context[Tux],
        user: discord.User,
    ) -> None:
        """Show information about a user."""
        embed = (
            self._create_info_embed(
                title=user.display_name,
                description="Here is some information about the user.",
                thumbnail_url=user.display_avatar.url,
                image_url=user.banner.url if user.banner else None,
            )
            .add_field(name="Bot?", value=self._format_bool(user.bot), inline=False)
            .add_field(name="Username", value=user.name, inline=False)
            .add_field(name="ID", value=str(user.id), inline=False)
            .add_field(
                name="Registered",
                value=self._format_datetime(user.created_at),
                inline=False,
            )
        )

        await ctx.send(embed=embed)

    async def _show_channel_info(
        self,
        ctx: commands.Context[Tux],
        channel: discord.abc.GuildChannel,
    ) -> None:
        """
        Show information about a channel.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        channel : discord.abc.GuildChannel
            The channel to get information about.
        """
        guild = ctx.guild
        assert guild

        embed: discord.Embed = (
            self._create_info_embed(
                title=f"#{channel.name}",
                description=getattr(channel, "topic", None) or "No topic available.",
                footer_text=f"ID: {channel.id} | Created: {channel.created_at.strftime('%B %d, %Y')}",
            )
            .add_field(name="Type", value=channel.__class__.__name__, inline=True)
            .add_field(name="Position", value=channel.position, inline=True)
            .add_field(
                name="Category",
                value=channel.category.name if channel.category else "None",
                inline=True,
            )
        )

        # Add specific fields based on channel type
        if isinstance(channel, discord.TextChannel):
            embed.add_field(
                name="Slowmode",
                value=f"{channel.slowmode_delay}s"
                if channel.slowmode_delay > 0
                else "None",
                inline=True,
            )
            embed.add_field(
                name="NSFW",
                value=self._format_bool(channel.nsfw),
                inline=True,
            )
        elif isinstance(channel, discord.VoiceChannel):
            embed.add_field(
                name="Bitrate",
                value=f"{channel.bitrate // 1000}kbps",
                inline=True,
            )
            embed.add_field(
                name="User Limit",
                value=channel.user_limit or "Unlimited",
                inline=True,
            )
        elif isinstance(channel, discord.ForumChannel):
            embed.add_field(
                name="Available Tags",
                value=len(channel.available_tags),
                inline=True,
            )
            embed.add_field(
                name="Default Layout",
                value=str(channel.default_layout),
                inline=True,
            )

        await ctx.send(embed=embed)

    async def _show_role_info(
        self,
        ctx: commands.Context[Tux],
        role: discord.Role,
    ) -> None:
        """
        Show information about a role.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        role : discord.Role
            The role to get information about.
        """
        guild = ctx.guild
        assert guild

        embed: discord.Embed = (
            self._create_info_embed(
                title=role.name,
                description="Here is some information about the role.",
                footer_text=f"ID: {role.id} | Created: {role.created_at.strftime('%B %d, %Y')}",
                custom_color=role.color
                if role.color != discord.Color.default()
                else discord.Color.blurple(),
            )
            .add_field(
                name="Color",
                value=f"#{role.color.value:06x}"
                if role.color != discord.Color.default()
                else "Default",
                inline=True,
            )
            .add_field(name="Position", value=role.position, inline=True)
            .add_field(
                name="Mentionable",
                value=self._format_bool(role.mentionable),
                inline=True,
            )
            .add_field(name="Hoisted", value=self._format_bool(role.hoist), inline=True)
            .add_field(
                name="Managed",
                value=self._format_bool(role.managed),
                inline=True,
            )
            .add_field(name="Members", value=len(role.members), inline=True)
            .add_field(
                name="Permissions",
                value=", ".join(
                    perm.replace("_", " ").title()
                    for perm, value in role.permissions
                    if value
                )[:1024]
                or "None",
                inline=False,
            )
        )

        await ctx.send(embed=embed)

    async def _show_emoji_info(
        self,
        ctx: commands.Context[Tux],
        emoji: discord.Emoji,
    ) -> None:
        """
        Show information about an emoji.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        emoji : discord.Emoji
            The emoji to get information about.
        """
        embed = (
            self._create_info_embed(
                title=emoji.name,
                description=f"Here is some information about the emoji.\n\n{emoji}",
                thumbnail_url=emoji.url,
                footer_text=f"ID: {emoji.id} | Created: {emoji.created_at.strftime('%B %d, %Y')}",
            )
            .add_field(
                name="Animated",
                value=self._format_bool(emoji.animated),
                inline=True,
            )
            .add_field(
                name="Managed",
                value=self._format_bool(emoji.managed),
                inline=True,
            )
            .add_field(
                name="Available",
                value=self._format_bool(emoji.available),
                inline=True,
            )
            .add_field(
                name="Requires Colons",
                value=self._format_bool(emoji.require_colons),
                inline=True,
            )
        )

        await ctx.send(embed=embed)

    async def _show_sticker_info(
        self,
        ctx: commands.Context[Tux],
        sticker: discord.GuildSticker,
    ) -> None:
        """
        Show information about a sticker.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        sticker : discord.GuildSticker
            The sticker to get information about.
        """
        embed: discord.Embed = (
            self._create_info_embed(
                title=sticker.name,
                description="Here is some information about the sticker.",
                thumbnail_url=sticker.url,
                footer_text=f"ID: {sticker.id} | Created: {sticker.created_at.strftime('%B %d, %Y')}",
            )
            .add_field(name="Format", value=str(sticker.format), inline=True)
            .add_field(
                name="Available",
                value=self._format_bool(sticker.available),
                inline=True,
            )
        )

        await ctx.send(embed=embed)

    async def _show_message_info(
        self,
        ctx: commands.Context[Tux],
        message: discord.Message,
    ) -> None:
        """
        Show information about a message.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        message : discord.Message
            The message to get information about.
        """
        # Handle channel display name based on channel type

        if isinstance(
            message.channel,
            (
                discord.TextChannel,
                discord.VoiceChannel,
                discord.Thread,
                discord.ForumChannel,
            ),
        ):
            channel_display = f"#{message.channel.name}"
            channel_mention = message.channel.mention
        else:
            # For DMs or other channel types
            channel_display = str(message.channel)
            channel_mention = str(message.channel)

        embed: discord.Embed = (
            self._create_info_embed(
                title=f"Message in {channel_display}",
                description=message.content[:2000]
                + ("..." if len(message.content) > 2000 else ""),
                footer_text=f"ID: {message.id} | Created: {message.created_at.strftime('%B %d, %Y')}",
            )
            .add_field(name="Author", value=message.author.mention, inline=True)
            .add_field(name="Channel", value=channel_mention, inline=True)
            .add_field(
                name="Jump",
                value=f"[Jump to Message]({message.jump_url})",
                inline=True,
            )
            .add_field(name="Attachments", value=len(message.attachments), inline=True)
            .add_field(name="Embeds", value=len(message.embeds), inline=True)
            .add_field(name="Reactions", value=len(message.reactions), inline=True)
        )

        await ctx.send(embed=embed)

    async def _show_invite_info(
        self,
        ctx: commands.Context[Tux],
        invite: discord.Invite,
    ) -> None:
        """
        Show information about an invite.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        invite : discord.Invite
            The invite to get information about.
        """
        embed: discord.Embed = (
            self._create_info_embed(
                title=f"Invite to {getattr(invite.guild, 'name', 'Unknown Server') if invite.guild else 'Unknown Server'}",
                description=f"**Code:** {invite.code}",
                footer_text=f"ID: {invite.id} | Created: {invite.created_at.strftime('%B %d, %Y')}"
                if invite.created_at
                else f"ID: {invite.id}",
            )
            .add_field(
                name="Guild",
                value=getattr(invite.guild, "name", "Unknown")
                if invite.guild
                else "Unknown",
                inline=True,
            )
            .add_field(
                name="Channel",
                value=getattr(invite.channel, "mention", "Unknown")
                if invite.channel
                else "Unknown",
                inline=True,
            )
            .add_field(
                name="Inviter",
                value=getattr(invite.inviter, "mention", "Unknown")
                if invite.inviter
                else "Unknown",
                inline=True,
            )
            .add_field(
                name="Uses",
                value=f"{invite.uses}/{invite.max_uses}"
                if invite.max_uses
                else f"{invite.uses}/∞",
                inline=True,
            )
            .add_field(
                name="Expires",
                value=discord.utils.format_dt(invite.expires_at, "R")
                if invite.expires_at
                else "Never",
                inline=True,
            )
            .add_field(
                name="Temporary",
                value=self._format_bool(invite.temporary or False),
                inline=True,
            )
        )

        await ctx.send(embed=embed)

    async def _show_thread_info(
        self,
        ctx: commands.Context[Tux],
        thread: discord.Thread,
    ) -> None:
        """
        Show information about a thread.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        thread : discord.Thread
            The thread to get information about.
        """
        embed: discord.Embed = (
            self._create_info_embed(
                title=f"Thread: {thread.name}",
                description=getattr(thread, "topic", None) or "No topic available.",
                footer_text=f"ID: {thread.id} | Created: {thread.created_at.strftime('%B %d, %Y') if thread.created_at else 'Unknown'}",
            )
            .add_field(name="Type", value=thread.__class__.__name__, inline=True)
            .add_field(
                name="Owner",
                value=thread.owner.mention if thread.owner else "Unknown",
                inline=True,
            )
            .add_field(
                name="Parent",
                value=thread.parent.mention if thread.parent else "None",
                inline=True,
            )
            .add_field(
                name="Archived",
                value=self._format_bool(thread.archived),
                inline=True,
            )
            .add_field(
                name="Locked",
                value=self._format_bool(thread.locked),
                inline=True,
            )
            .add_field(name="Message Count", value=thread.message_count, inline=True)
        )

        await ctx.send(embed=embed)

    async def _show_event_info(
        self,
        ctx: commands.Context[Tux],
        event: discord.ScheduledEvent,
    ) -> None:
        """
        Show information about a scheduled event.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        event : discord.ScheduledEvent
            The scheduled event to get information about.
        """
        embed: discord.Embed = (
            self._create_info_embed(
                title=event.name,
                description=event.description or "No description available.",
                footer_text=f"ID: {event.id}",
            )
            .add_field(name="Status", value=str(event.status).title(), inline=True)
            .add_field(
                name="Privacy",
                value=str(event.privacy_level).title(),
                inline=True,
            )
            .add_field(
                name="Entity Type",
                value=str(event.entity_type).title(),
                inline=True,
            )
            .add_field(
                name="Start Time",
                value=discord.utils.format_dt(event.start_time, "F")
                if event.start_time
                else "Not set",
                inline=True,
            )
            .add_field(
                name="End Time",
                value=discord.utils.format_dt(event.end_time, "F")
                if event.end_time
                else "Not set",
                inline=True,
            )
            .add_field(name="User Count", value=event.user_count, inline=True)
        )

        await ctx.send(embed=embed)

    async def paginated_embed(
        self,
        ctx: commands.Context[Tux],
        title: str,
        list_type: str,
        guild_name: str,
        items: Iterable[str],
        chunk_size: int,
    ) -> None:
        """
        Send a paginated embed.

        Parameters
        ----------
        ctx : commands.Context
            The context object associated with the command.
        title : str
            The title of the embed.
        list_type : str
            The type of list (e.g., roles, emotes).
        guild_name : str
            The name of the guild.
        items : Iterable[str]
            The items to display in the embed.
        chunk_size : int
            The size of each chunk for pagination.
        """
        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=title,
            custom_color=discord.Color.blurple(),
        )
        chunks: list[list[str]] = list(self._chunks(iter(items), chunk_size))

        if not chunks:
            embed.description = "No items available."
            await ctx.send(embed=embed)
            return

        menu: ViewMenu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
        for chunk in chunks:
            page_embed: discord.Embed = embed.copy()
            page_embed.description = (
                f"{list_type.capitalize()} list for {guild_name}:\n{' '.join(chunk)}"
            )
            menu.add_page(page_embed)

        buttons = [
            ViewButton.go_to_first_page(),
            ViewButton.back(),
            ViewButton.next(),
            ViewButton.go_to_last_page(),
            ViewButton.end_session(),
        ]

        for button in buttons:
            menu.add_button(button)

        await menu.start()

    @staticmethod
    def _chunks(it: Iterator[str], size: int) -> Generator[list[str]]:
        """
        Split an iterator into chunks of a specified size.

        Parameters
        ----------
        it : Iterator[str]
            The input iterator to be split into chunks.
        size : int
            The size of each chunk.

        Yields
        ------
        List[str]
            A list containing a chunk of elements from the input iterator. The last
            list may contain fewer elements if there are not enough remaining to fill
            a complete chunk.
        """
        chunk: list[str] = []
        for item in it:
            chunk.append(item)
            if len(chunk) == size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk


async def setup(bot: Tux) -> None:
    """Set up the Info cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Info(bot))
