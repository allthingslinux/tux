"""Bookmark service for saving and managing Discord messages.

This module provides functionality to bookmark Discord messages through reactions,
allowing users to save important messages for later reference. Messages can be
bookmarked by reacting with specific emojis, and bookmarks are stored in user DMs.
"""

from __future__ import annotations

import io

import aiohttp
import discord
from discord.abc import Messageable
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.constants import ADD_BOOKMARK, EMBED_MAX_DESC_LENGTH, REMOVE_BOOKMARK
from tux.ui.embeds import EmbedCreator


class Bookmarks(BaseCog):
    """Discord cog for bookmarking messages.

    This cog allows users to bookmark messages by reacting with specific emojis,
    and manages the storage and retrieval of bookmarked messages.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Bookmarks cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        self.add_bookmark_emojis = ADD_BOOKMARK
        self.remove_bookmark_emojis = REMOVE_BOOKMARK
        self.valid_emojis = self.add_bookmark_emojis + self.remove_bookmark_emojis
        self.session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        """Clean up the cog, closing the aiohttp session."""
        await self.session.close()

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        """
        Handle bookmarking messages via reactions.

        This listener checks for specific reaction emojis on messages and triggers
        the bookmarking or unbookmarking process accordingly.

        Parameters
        ----------
        payload : discord.RawReactionActionEvent
            The event payload containing information about the reaction.
        """
        # If the bot reacted to the message, or the user is the bot, or the emoji is not valid, return
        if (
            not self.bot.user
            or payload.user_id == self.bot.user.id
            or not payload.emoji.name
        ):
            return

        # If the emoji is not valid, return
        if payload.emoji.name not in self.valid_emojis:
            return

        try:
            # Get the user who reacted to the message
            user = self.bot.get_user(payload.user_id) or await self.bot.fetch_user(
                payload.user_id,
            )

            # Get the channel where the reaction was added
            channel = self.bot.get_channel(payload.channel_id)
            if channel is None:
                channel = await self.bot.fetch_channel(payload.channel_id)

            # If the channel is not messageable, return
            if not isinstance(channel, Messageable):
                logger.warning(
                    f"Bookmark reaction in non-messageable channel {payload.channel_id}.",
                )
                return

            # Get the message that was reacted to
            message = await channel.fetch_message(payload.message_id)

        # If the message is not found, return
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to fetch data for bookmark event: {e}")
            return

        # If the emoji is the add bookmark emoji, add the bookmark
        if payload.emoji.name in self.add_bookmark_emojis:
            await self.add_bookmark(user, message)

        # Ensures were in a users DMs before removing (to fix an issue with being able to remove messages anywhere)
        if not isinstance(channel, discord.DMChannel):
            return

        # If the emoji is the remove bookmark emoji and reaction is on the bot, remove the bookmark
        if (
            payload.emoji.name in self.remove_bookmark_emojis
            and message.author is self.bot.user
        ):
            await self.remove_bookmark(message)

    async def add_bookmark(self, user: discord.User, message: discord.Message) -> None:
        """
        Send a bookmarked message to the user's DMs.

        Parameters
        ----------
        user : discord.User
            The user who bookmarked the message.
        message : discord.Message
            The message to be bookmarked.
        """
        embed = self._create_bookmark_embed(message)
        files = await self._get_files_from_message(message)

        try:
            dm_message = await user.send(embed=embed, files=files)
            await dm_message.add_reaction(self.remove_bookmark_emojis)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.warning(f"Could not send DM to {user.name} ({user.id}): {e}")

            try:
                await message.channel.send(
                    f"{user.mention}, I couldn't send you a DM. Please check your privacy settings.",
                )

            except (discord.Forbidden, discord.HTTPException) as e2:
                logger.error(
                    f"Could not send notification in channel {message.channel.id}: {e2}",
                )

    @staticmethod
    async def remove_bookmark(message: discord.Message) -> None:
        """
        Delete a bookmark DM when the user reacts with the remove emoji.

        Parameters
        ----------
        message : discord.Message
            The bookmark message in the user's DMs to be deleted.
        """
        try:
            await message.delete()

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to delete bookmark message {message.id}: {e}")

    async def _get_files_from_attachments(
        self,
        message: discord.Message,
        files: list[discord.File],
    ) -> None:
        """Extract image files from message attachments.

        Parameters
        ----------
        message : discord.Message
            The message to extract attachments from.
        files : list[discord.File]
            The list to append extracted files to.
        """
        for attachment in message.attachments:
            if len(files) >= 10:
                break

            if attachment.content_type and "image" in attachment.content_type:
                try:
                    files.append(await attachment.to_file())
                except (discord.HTTPException, discord.NotFound) as e:
                    logger.error(f"Failed to get attachment {attachment.filename}: {e}")

    async def _get_files_from_stickers(
        self,
        message: discord.Message,
        files: list[discord.File],
    ) -> None:
        """Extract image files from message stickers.

        Parameters
        ----------
        message : discord.Message
            The message to extract stickers from.
        files : list[discord.File]
            The list to append extracted files to.
        """
        if len(files) >= 10:
            return

        for sticker in message.stickers:
            if len(files) >= 10:
                break

            if sticker.format in {
                discord.StickerFormatType.png,
                discord.StickerFormatType.apng,
            }:
                try:
                    sticker_bytes = await sticker.read()
                    files.append(
                        discord.File(
                            io.BytesIO(sticker_bytes),
                            filename=f"{sticker.name}.png",
                        ),
                    )
                except (discord.HTTPException, discord.NotFound) as e:
                    logger.error(f"Failed to read sticker {sticker.name}: {e}")

    async def _get_files_from_embeds(
        self,
        message: discord.Message,
        files: list[discord.File],
    ) -> None:
        """Extract image files from message embeds.

        Parameters
        ----------
        message : discord.Message
            The message to extract embeds from.
        files : list[discord.File]
            The list to append extracted files to.
        """
        if len(files) >= 10:
            return

        for embed in message.embeds:
            if len(files) >= 10:
                break

            if embed.image and embed.image.url:
                try:
                    async with self.session.get(embed.image.url) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            filename = embed.image.url.split("/")[-1].split("?")[0]
                            files.append(
                                discord.File(io.BytesIO(data), filename=filename),
                            )
                except aiohttp.ClientError as e:
                    logger.error(f"Failed to fetch embed image {embed.image.url}: {e}")

    async def _get_files_from_message(
        self,
        message: discord.Message,
    ) -> list[discord.File]:
        """
        Gathers images from a message to be sent as attachments.

        This function collects images from attachments, stickers, and embeds,
        respecting Discord's 10-file limit.

        Parameters
        ----------
        message : discord.Message
            The message to extract files from.

        Returns
        -------
        list[discord.File]
            A list of files to be attached to the bookmark message.
        """
        files: list[discord.File] = []

        await self._get_files_from_attachments(message, files)
        await self._get_files_from_stickers(message, files)
        await self._get_files_from_embeds(message, files)

        return files

    def _create_bookmark_embed(self, message: discord.Message) -> discord.Embed:
        """
        Create an embed for a bookmarked message.

        This function constructs a detailed embed that includes the message content,
        author, attachments, and other contextual information.

        Parameters
        ----------
        message : discord.Message
            The message to create an embed from.

        Returns
        -------
        discord.Embed
            The generated bookmark embed.
        """
        # Get the content of the message
        content = message.content or ""

        # Truncate the content if it's too long
        if len(content) > EMBED_MAX_DESC_LENGTH:
            content = f"{content[: EMBED_MAX_DESC_LENGTH - 4]}..."

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            title="Message Bookmarked",
            description=f"{content}"
            if content
            else "> No content available to display",
        )

        # Add author to the embed
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url,
        )

        # Add reference to the embed if it exists
        if message.reference and message.reference.resolved:
            ref_msg = message.reference.resolved
            if isinstance(ref_msg, discord.Message):
                embed.add_field(
                    name="Replying to",
                    value=f"[Click Here]({ref_msg.jump_url})",
                )

        # Add jump to message to the embed
        embed.add_field(
            name="Jump to Message",
            value=f"[Click Here]({message.jump_url})",
        )

        # Add attachments to the embed
        if message.attachments:
            attachments = "\n".join(
                f"[{a.filename}]({a.url})" for a in message.attachments
            )
            embed.add_field(name="Attachments", value=attachments, inline=False)

        # Add stickers to the embed
        if message.stickers:
            stickers = "\n".join(f"[{s.name}]({s.url})" for s in message.stickers)
            embed.add_field(name="Stickers", value=stickers, inline=False)

        # Handle embeds
        if message.embeds:
            embed.add_field(
                name="Contains Embeds",
                value="Original message contains embeds which are not shown here.",
                inline=False,
            )

        # Add footer to the embed
        if message.guild and isinstance(
            message.channel,
            discord.TextChannel | discord.Thread,
        ):
            embed.set_footer(text=f"In #{message.channel.name} on {message.guild.name}")

        # Add timestamp to the embed
        embed.timestamp = message.created_at

        return embed


async def setup(bot: Tux) -> None:
    """Set up the Bookmarks cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Bookmarks(bot))
