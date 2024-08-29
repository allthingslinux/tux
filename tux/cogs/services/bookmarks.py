import discord
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


class Bookmarks(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if str(payload.emoji) != "🔖":
            return

        # Fetch the channel where the reaction was added
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            logger.error(f"Channel not found for ID: {payload.channel_id}")
            return

        # Fetch the message that was reacted to
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            logger.error(f"Message not found for ID: {payload.message_id}")
            return
        except (discord.Forbidden, discord.HTTPException) as fetch_error:
            logger.error(f"Failed to fetch message: {fetch_error}")
            return

        # Create an embed for the bookmarked message
        embed = self._create_bookmark_embed(message)

        # Get the user who reacted to the message
        user = self.bot.get_user(payload.user_id)
        if user is None:
            logger.error(f"User not found for ID: {payload.user_id}")
            return

        # Send the bookmarked message to the user
        await self._send_bookmark(user, message, embed, payload.emoji)

    def _create_bookmark_embed(
        self,
        message: discord.Message,
    ) -> discord.Embed:
        if message.content.length > CONST.EMBED_MAX_DESC_LENGTH:
            message.content = f"{message.content[:CONST.EMBED_MAX_DESC_LENGTH - 3]}..."

        embed = EmbedCreator.create_info_embed(
            title="Message Bookmarked",
            description=f"> {message.content}",
        )

        embed.add_field(name="Author", value=message.author.name, inline=False)

        embed.add_field(name="Jump to Message", value=f"[Click Here]({message.jump_url})", inline=False)

        if message.attachments:
            attachments_info = "\n".join([attachment.url for attachment in message.attachments])
            embed.add_field(name="Attachments", value=attachments_info, inline=False)

        return embed

    async def _send_bookmark(
        self,
        user: discord.User,
        message: discord.Message,
        embed: discord.Embed,
        emoji: str,
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
            await user.send(embed=embed)

        except (discord.Forbidden, discord.HTTPException) as dm_error:
            logger.error(f"Cannot send a DM to {user.name}: {dm_error}")

            notify_message = await message.channel.send(
                f"{user.mention}, I couldn't send you a DM. Please make sure your DMs are open for bookmarks to work.",
            )

            await notify_message.delete(delay=30)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bookmarks(bot))
