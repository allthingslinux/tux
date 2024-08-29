import discord
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class Bookmarks(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if str(payload.emoji) == "🔖":
            try:
                channel = self.bot.get_channel(payload.channel_id)
                if channel is None:
                    logger.error("Channel not found")
                    return

                message = await channel.fetch_message(payload.message_id)
                if message is None:
                    logger.error("Message not found")
                    return

                message_link = message.jump_url
                message_contents = message.content
                message_attachments = message.attachments
                author_username = message.author.name

                embed = EmbedCreator.create_info_embed(
                    title="Message Bookmarked",
                    description=f"> {message_contents}",
                )
                embed.add_field(name="Author", value=author_username, inline=False)
                embed.add_field(name="Jump to Message", value=f"[Click Here]({message_link})", inline=False)

                if message_attachments:
                    attachments_info = "\n".join([attachment.url for attachment in message_attachments])
                    embed.add_field(name="Attachments", value=attachments_info, inline=False)

                try:
                    user = self.bot.get_user(payload.user_id)
                    if user is not None:
                        await user.send(embed=embed)
                    else:
                        logger.error(f"User not found for ID: {payload.user_id}")
                except (discord.Forbidden, discord.HTTPException) as e:
                    logger.error(f"An error occurred while bookmarking {message_link} for {payload.user_id}: {e}")

            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                logger.error(f"Failed to process the reaction: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bookmarks(bot))
