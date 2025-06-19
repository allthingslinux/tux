from typing import cast

import discord
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.ui.embeds import EmbedCreator
from tux.utils.config import CONFIG
from tux.utils.constants import CONST


class Bookmarks(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

<<<<<<< HEAD
        self.valid_add_emojis = CONST.ADD_BOOKMARK
        self.valid_remove_emojis = CONST.REMOVE_BOOKMARK
        self.valid_emojis = CONST.ADD_BOOKMARK + CONST.REMOVE_BOOKMARK
=======
        self.valid_emojis: list[int | str] = CONFIG.ADD_BOOKMARK + CONFIG.REMOVE_BOOKMARK
        self.valid_add_emojis: list[int | str] = CONFIG.ADD_BOOKMARK
        self.valid_remove_emojis: list[int | str] = CONFIG.REMOVE_BOOKMARK
>>>>>>> b9c797a (wip changes)

    def _is_valid_emoji(self, emoji: discord.PartialEmoji, valid_list: list[int | str]) -> bool:
        # Helper for checking if an emoji is in the list in "settings.yml -> BOOKMARK_EMOJIS"
        return emoji.name in valid_list if emoji.id is None else emoji.id in valid_list

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
        Handle the addition of a reaction to a message.

        Parameters
        ----------
        payload : discord.RawReactionActionEvent
            The payload of the reaction event.

        Returns
        -------
        None
        """
        if not self._is_valid_emoji(payload.emoji, self.valid_emojis):
<<<<<<< HEAD
=======
            return

        # Get the user who reacted to the message
        user = self.bot.get_user(payload.user_id)
        if user is None:
<<<<<<< HEAD
<<<<<<< HEAD
            logger.error(f"User not found for ID: {payload.user_id}")
>>>>>>> b9c797a (wip changes)
            return
=======
            try:
                user = await self.bot.fetch_user(payload.user_id)
            except discord.NotFound:
                logger.error(f"User not found for ID: {payload.user_id}")
                return
            except (discord.Forbidden, discord.HTTPException) as fetch_error:
                logger.error(f"Failed to fetch user: {fetch_error}")
                return
>>>>>>> 217c364 (fix(bookmarks): improve emoji validation and error handling for user and channel fetching)

        # Get the user who reacted to the message
        user = self.bot.get_user(payload.user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(payload.user_id)
            except discord.NotFound:
                logger.error(f"User not found for ID: {payload.user_id}")
<<<<<<< HEAD
            except (discord.Forbidden, discord.HTTPException) as fetch_error:
                logger.error(f"Failed to fetch user: {fetch_error}")
            return
=======
                return
            except (discord.Forbidden, discord.HTTPException) as fetch_error:
                logger.error(f"Failed to fetch user: {fetch_error}")
                return

>>>>>>> 217c364 (fix(bookmarks): improve emoji validation and error handling for user and channel fetching)
=======
            try:
                user = await self.bot.fetch_user(payload.user_id)
            except discord.NotFound:
                logger.error(f"User not found for ID: {payload.user_id}")
            except (discord.Forbidden, discord.HTTPException) as fetch_error:
                logger.error(f"Failed to fetch user: {fetch_error}")
            return
>>>>>>> b8a4072 (added eletrons changes and fixed a warning)
        # Fetch the channel where the reaction was added
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except discord.NotFound:
                logger.error(f"Channel not found for ID: {payload.channel_id}")
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b8a4072 (added eletrons changes and fixed a warning)
            except (discord.Forbidden, discord.HTTPException) as fetch_error:
                logger.error(f"Failed to fetch channel: {fetch_error}")
            return

<<<<<<< HEAD
=======
=======
>>>>>>> 217c364 (fix(bookmarks): improve emoji validation and error handling for user and channel fetching)
                return
            except (discord.Forbidden, discord.HTTPException) as fetch_error:
                logger.error(f"Failed to fetch channel: {fetch_error}")
                return
<<<<<<< HEAD
>>>>>>> 217c364 (fix(bookmarks): improve emoji validation and error handling for user and channel fetching)
=======
>>>>>>> b8a4072 (added eletrons changes and fixed a warning)
=======
>>>>>>> 217c364 (fix(bookmarks): improve emoji validation and error handling for user and channel fetching)
        channel = cast(discord.TextChannel | discord.Thread, channel)

        # Fetch the message that was reacted to
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            logger.error(f"Message not found for ID: {payload.message_id}")
            return
        except (discord.Forbidden, discord.HTTPException) as fetch_error:
            logger.error(f"Failed to fetch message: {fetch_error}")
            return

        # check for what to do
        if self._is_valid_emoji(payload.emoji, self.valid_add_emojis):
            # Create an embed for the bookmarked message
            embed = await self._create_bookmark_embed(message)

            # Send the bookmarked message to the user
            await self._send_bookmark(user, message, embed, payload.emoji)

        elif self._is_valid_emoji(payload.emoji, self.valid_remove_emojis):
            await self._delete_bookmark(message, user)
        else:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            logger.error(
                "First emoji validation check passed but second emoji validation check failed. How the fuck did you get here?",
            )
=======
            logger.debug("Somehow you managed to get bast the first valid emoji check then failed the 2nd good job?")
>>>>>>> b9c797a (wip changes)
=======
            logger.error("How did you fail the 2nd check but passed the first?")
>>>>>>> 56bebaf (Added removing bookmarks from the bot's DMs)
=======
            logger.error(
                "First emoji validation check passed but second emoji validation check failed. How the fuck did you get here?",
            )
>>>>>>> b8a4072 (added eletrons changes and fixed a warning)
=======
            logger.error(
                "First emoji validation check passed but second emoji validation check failed. How the fuck did you get here?",
            )
>>>>>>> 217c364 (fix(bookmarks): improve emoji validation and error handling for user and channel fetching)
            return

    async def _create_bookmark_embed(
        self,
        message: discord.Message,
    ) -> discord.Embed:
        if len(message.content) > CONST.EMBED_MAX_DESC_LENGTH:
            message.content = f"{message.content[: CONST.EMBED_MAX_DESC_LENGTH - 3]}..."

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            title="Message Bookmarked",
            description=f"> {message.content}",
        )

        embed.add_field(name="Author", value=message.author.name, inline=False)

        embed.add_field(name="Jump to Message", value=f"[Click Here]({message.jump_url})", inline=False)
<<<<<<< HEAD
=======

        embed.add_field(
            name="Delete Bookmark",
            value=f"React with {CONFIG.REMOVE_BOOKMARK[0]} to delete this bookmark.",
            inline=False,
        )

<<<<<<< HEAD
>>>>>>> b8a4072 (added eletrons changes and fixed a warning)
=======
>>>>>>> 217c364 (fix(bookmarks): improve emoji validation and error handling for user and channel fetching)
        if message.attachments:
            attachments_info = "\n".join([attachment.url for attachment in message.attachments])
            embed.add_field(name="Attachments", value=attachments_info, inline=False)

        return embed

    async def _delete_bookmark(self, message: discord.Message, user: discord.User) -> None:
<<<<<<< HEAD
<<<<<<< HEAD
        if message.author is not self.bot.user:
            return
        await message.delete()
=======
        logger.debug("you got to the delte function")
=======
>>>>>>> 56bebaf (Added removing bookmarks from the bot's DMs)
        if message.author is not self.bot.user:
            return
<<<<<<< HEAD
>>>>>>> b9c797a (wip changes)
=======
        await message.delete()
>>>>>>> 56bebaf (Added removing bookmarks from the bot's DMs)

    @staticmethod
    async def _send_bookmark(
        user: discord.User,
        message: discord.Message,
        embed: discord.Embed,
        emoji: discord.PartialEmoji,
    ) -> None:
        """
        Send a bookmarked message to the user.

        Parameters
        ----------
        user : discord.User
            The user to send the bookmarked message to.
        message : discord.Message
            The message that was bookmarked.
        embed : discord.Embed
            The embed to send to the user.
        emoji : str
            The emoji that was reacted to the message.
        """

        try:
            dm_message = await user.send(embed=embed)
            await dm_message.add_reaction(CONST.REMOVE_BOOKMARK)

        except (discord.Forbidden, discord.HTTPException) as dm_error:
            logger.error(f"Cannot send a DM to {user.name}: {dm_error}")

            notify_message = await message.channel.send(
                f"{user.mention}, I couldn't send you a DM. Please make sure your DMs are open for bookmarks to work.",
            )

            await notify_message.delete(delay=30)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Bookmarks(bot))
