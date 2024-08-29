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

                embed = EmbedCreator.create_info_embed(
                    title="Message Bookmarked",
                    description=f"> {message.content}",
                )
                embed.add_field(name="Author", value=message.author.name, inline=False)
                embed.add_field(name="Jump to Message", value=f"[Click Here]({message.jump_url})", inline=False)

                if message.attachments:
                    attachments_info = "\n".join([attachment.url for attachment in message.attachments])
                    embed.add_field(name="Attachments", value=attachments_info, inline=False)

                try:
                    user = self.bot.get_user(payload.user_id)
                    if user is not None:
                        await user.send(embed=embed)
                        await message.remove_reaction(payload.emoji, user)
                    else:
                        logger.error(f"User not found for ID: {payload.user_id}")
                except (discord.Forbidden, discord.HTTPException):
                    logger.error(f"Cannot send a DM to {user.name}. They may have DMs turned off.")
                    await message.remove_reaction(payload.emoji, user)
                    temp_message = await channel.send(
                        f"{user.mention}, I couldn't send you a DM make sure your DMs are open for bookmarks to work",
                    )
                    await temp_message.delete(delay=30)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                logger.error(f"Failed to process the reaction: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bookmarks(bot))
